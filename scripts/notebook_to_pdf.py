#!/usr/bin/env python3
"""
Конвертация Jupyter ноутбуков в PDF.

Использование:
    python notebook_to_pdf.py notebook.ipynb [output.pdf]
    python notebook_to_pdf.py --all  # Конвертировать все ноутбуки в папке notebooks/

Требования:
    pip install nbconvert
    # Для LaTeX PDF:
    sudo apt install texlive-xetex texlive-fonts-recommended texlive-lang-cyrillic
    # Или для webpdf (проще):
    pip install pyppeteer
"""

import argparse
import subprocess
import sys
from pathlib import Path


def convert_via_html(notebook_path: Path, output_path: Path) -> bool:
    """
    Конвертация через HTML (наиболее надёжный способ).
    Требует: pip install nbconvert
    """
    html_path = output_path.with_suffix('.html')
    
    # Шаг 1: notebook -> HTML
    cmd = [
        sys.executable, '-m', 'nbconvert',
        '--to', 'html',
        '--output', str(html_path.stem),
        '--output-dir', str(output_path.parent),
        str(notebook_path)
    ]
    
    print(f"  Конвертация в HTML: {notebook_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  Ошибка HTML: {result.stderr}")
        return False
    
    print(f"  ✓ HTML создан: {html_path.name}")
    return True


def convert_via_latex(notebook_path: Path, output_path: Path) -> bool:
    """
    Конвертация через LaTeX (качественный PDF).
    Требует: texlive-xetex, texlive-lang-cyrillic
    """
    cmd = [
        sys.executable, '-m', 'nbconvert',
        '--to', 'pdf',
        '--output', str(output_path.stem),
        '--output-dir', str(output_path.parent),
        str(notebook_path)
    ]
    
    print(f"  Конвертация в PDF (LaTeX): {notebook_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  Ошибка LaTeX: {result.stderr[:500]}")
        return False
    
    print(f"  ✓ PDF создан: {output_path.name}")
    return True


def convert_via_webpdf(notebook_path: Path, output_path: Path) -> bool:
    """
    Конвертация через WebPDF (без LaTeX, использует браузер).
    Требует: pip install nbconvert[webpdf] pyppeteer
    """
    cmd = [
        sys.executable, '-m', 'nbconvert',
        '--to', 'webpdf',
        '--allow-chromium-download',
        '--output', str(output_path.stem),
        '--output-dir', str(output_path.parent),
        str(notebook_path)
    ]
    
    print(f"  Конвертация в PDF (WebPDF): {notebook_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  Ошибка WebPDF: {result.stderr[:500]}")
        return False
    
    print(f"  ✓ PDF создан: {output_path.name}")
    return True


def convert_notebook(notebook_path: Path, output_path: Path = None, method: str = 'auto') -> bool:
    """
    Конвертировать ноутбук в PDF.
    
    Args:
        notebook_path: Путь к .ipynb файлу
        output_path: Путь к выходному PDF (опционально)
        method: 'latex', 'webpdf', 'html', или 'auto'
    
    Returns:
        True если успешно
    """
    notebook_path = Path(notebook_path)
    
    if not notebook_path.exists():
        print(f"Файл не найден: {notebook_path}")
        return False
    
    if output_path is None:
        output_path = notebook_path.with_suffix('.pdf')
    else:
        output_path = Path(output_path)
    
    # Создаём директорию если нужно
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📓 {notebook_path.name}")
    
    if method == 'auto':
        # Пробуем методы по порядку
        methods = [
            ('webpdf', convert_via_webpdf),
            ('latex', convert_via_latex),
            ('html', convert_via_html),
        ]
        
        for name, func in methods:
            try:
                if func(notebook_path, output_path):
                    return True
            except Exception as e:
                print(f"  {name} не удался: {e}")
                continue
        
        print(f"  ✗ Все методы не удались")
        return False
    
    elif method == 'latex':
        return convert_via_latex(notebook_path, output_path)
    elif method == 'webpdf':
        return convert_via_webpdf(notebook_path, output_path)
    elif method == 'html':
        return convert_via_html(notebook_path, output_path)
    else:
        print(f"Неизвестный метод: {method}")
        return False


def convert_all_notebooks(notebooks_dir: Path, output_dir: Path = None, method: str = 'auto') -> dict:
    """
    Конвертировать все ноутбуки в директории.
    
    Returns:
        dict с результатами {path: success}
    """
    notebooks_dir = Path(notebooks_dir)
    
    if output_dir is None:
        output_dir = notebooks_dir.parent / 'pdf'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    notebooks = list(notebooks_dir.glob('*.ipynb'))
    
    if not notebooks:
        print(f"Ноутбуки не найдены в {notebooks_dir}")
        return {}
    
    print(f"Найдено {len(notebooks)} ноутбуков в {notebooks_dir}")
    print(f"Выходная директория: {output_dir}")
    print("=" * 60)
    
    results = {}
    
    for nb in sorted(notebooks):
        output_path = output_dir / nb.with_suffix('.pdf').name
        results[nb] = convert_notebook(nb, output_path, method)
    
    # Итоги
    print("\n" + "=" * 60)
    success = sum(results.values())
    print(f"Готово: {success}/{len(results)} ноутбуков конвертировано")
    
    if success < len(results):
        print("\nНе удалось конвертировать:")
        for nb, ok in results.items():
            if not ok:
                print(f"  - {nb.name}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Конвертация Jupyter ноутбуков в PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s notebook.ipynb                    # Конвертировать один ноутбук
  %(prog)s notebook.ipynb output.pdf         # С указанием выходного файла
  %(prog)s --all                             # Все ноутбуки в notebooks/
  %(prog)s --all --method latex              # Использовать LaTeX
  %(prog)s --all --output-dir ./pdf          # Указать выходную директорию

Методы конвертации:
  auto   - Автоматический выбор (по умолчанию)
  webpdf - Через браузер (требует pyppeteer)
  latex  - Через LaTeX (требует texlive)
  html   - Только HTML (без PDF)
        """
    )
    
    parser.add_argument('notebook', nargs='?', help='Путь к .ipynb файлу')
    parser.add_argument('output', nargs='?', help='Путь к выходному PDF')
    parser.add_argument('--all', action='store_true', help='Конвертировать все ноутбуки')
    parser.add_argument('--notebooks-dir', type=Path, default=None,
                        help='Директория с ноутбуками (по умолчанию: notebooks/)')
    parser.add_argument('--output-dir', type=Path, default=None,
                        help='Директория для PDF (по умолчанию: pdf/)')
    parser.add_argument('--method', choices=['auto', 'latex', 'webpdf', 'html'],
                        default='auto', help='Метод конвертации')
    
    args = parser.parse_args()
    
    # Определяем корневую директорию проекта
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    
    if args.all:
        notebooks_dir = args.notebooks_dir or (project_dir / 'notebooks')
        output_dir = args.output_dir or (project_dir / 'pdf')
        
        results = convert_all_notebooks(notebooks_dir, output_dir, args.method)
        sys.exit(0 if all(results.values()) else 1)
    
    elif args.notebook:
        notebook_path = Path(args.notebook)
        output_path = Path(args.output) if args.output else None
        
        success = convert_notebook(notebook_path, output_path, args.method)
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
