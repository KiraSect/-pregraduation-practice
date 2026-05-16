import os
import sys
import ast
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


def extract_functions(file_path: str) -> list:
    source = Path(file_path).read_text(encoding="utf-8")
    tree = ast.parse(source)

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [arg.arg for arg in node.args.args]
            docstring = ast.get_docstring(node) or ""

            func_source = ast.get_source_segment(source, node)

            functions.append({
                "name": node.name,
                "args": args,
                "docstring": docstring,
                "source": func_source
            })
    return functions


def generate_tests(functions: list, module_name: str) -> str:
    code = "\n\n".join(f["source"] for f in functions)

    prompt = f"""
ты senior python qa engineer.

сгенерируй качественные pytest-тесты для функций ниже.

правила:
- импортируй функции из модуля {module_name}
- используй pytest
- каждый тест отдельной функцией
- добавь проверки normal case и edge case
- если есть исключения -> используй pytest.raises
- где подходит используй pytest.mark.parametrize
- не добавляй пояснения
- верни только python-код

код:
{code}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "ты генерируешь только валидный pytest-код"
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.15
    )

    result = response.choices[0].message.content.strip()
    return (
        result
        .replace("```python", "")
        .replace("```", "")
        .strip()
    )


def check_tests_run(test_file: str) -> bool:
    try:
        ast.parse(Path(test_file).read_text(encoding="utf-8"))

        result = subprocess.run(
            ["pytest", test_file, "-q"],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(result.stdout)

        if result.returncode == 0:
            print("тесты успешно прошли")
            return True

        print("pytest вернул ошибку")
        print(result.stderr[-400:])
        return False

    except Exception as e:
        print(f"ошибка проверки: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("использование python main.py <путь_к_файлу.py>")
        sys.exit(1)

    source_file = sys.argv[1]

    if not GROQ_API_KEY:
        print("ошибка: не указан GROQ_API_KEY в .env")
        sys.exit(1)

    if not os.path.exists(source_file):
        print(f"файл {source_file} не найден.")
        sys.exit(1)

    print(f"анализирую {source_file}")
    functions = extract_functions(source_file)
    if not functions:
        print("в файле нет функций.")
        return

    print(f"найдено функций: {len(functions)}")
    for f in functions:
        print(f"  - {f['name']}({', '.join(f['args'])})")

    module_name = Path(source_file).stem

    print("\nгенерирую тесты")
    test_code = generate_tests(functions, module_name)

    test_file = f"test_{module_name}.py"
    Path(test_file).write_text(test_code, encoding="utf-8")
    print(f"тесты сохранены в {test_file}")

    print("\nпроверка тестов:")
    check_tests_run(test_file)


if __name__ == "__main__":
    main()
