#!/usr/bin/env python3
"""
Spec Builder — скрипт для сборки частей спецификации в единый SPEC.md.

Использование:
    python build_spec.py          # Генерирует SPEC.md
    python build_spec.py --check  # Проверяет актуальность SPEC.md

Алгоритм:
    1. Найти все *.md файлы в spec/
    2. Отсортировать по числовому префиксу
    3. Извлечь заголовки первого уровня для оглавления
    4. Собрать в единый файл с оглавлением
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional


# Паттерн для имени файла: NN-*.md где NN — числовой префикс
FILENAME_PATTERN = re.compile(r'^(\d+)-.*\.md$')

# Паттерн для заголовка первого уровня
HEADING_PATTERN = re.compile(r'^#\s+(.+)$', re.MULTILINE)


def get_script_dir() -> Path:
    """Возвращает директорию, в которой находится скрипт."""
    return Path(__file__).parent.resolve()


def get_spec_dir() -> Path:
    """Возвращает путь к директории spec/ относительно скрипта."""
    return get_script_dir().parent / 'spec'


def get_output_path() -> Path:
    """Возвращает путь к выходному файлу SPEC.md."""
    return get_script_dir().parent / 'SPEC.md'


def find_spec_files(spec_dir: Path) -> List[Tuple[int, Path]]:
    """
    Находит все файлы спецификации в директории spec/.
    
    Возвращает список кортежей (числовой_префикс, путь_к_файлу),
    отсортированный по числовому префиксу.
    
    Файлы с некорректным форматом имени пропускаются с предупреждением.
    """
    if not spec_dir.exists():
        return []
    
    files: List[Tuple[int, Path]] = []
    prefixes_seen: dict[int, Path] = {}
    
    for file_path in spec_dir.iterdir():
        if not file_path.is_file():
            continue
            
        match = FILENAME_PATTERN.match(file_path.name)
        if not match:
            print(f"Предупреждение: файл '{file_path.name}' не соответствует формату NN-*.md, пропускаем",
                  file=sys.stderr)
            continue
        
        prefix = int(match.group(1))
        
        # Проверка на дубликаты числового префикса
        if prefix in prefixes_seen:
            print(f"Ошибка: дублирующийся числовой префикс {prefix:02d}:",
                  file=sys.stderr)
            print(f"  - {prefixes_seen[prefix].name}", file=sys.stderr)
            print(f"  - {file_path.name}", file=sys.stderr)
            sys.exit(1)
        
        prefixes_seen[prefix] = file_path
        files.append((prefix, file_path))
    
    # Сортировка по числовому префиксу
    files.sort(key=lambda x: x[0])
    return files


def extract_first_heading(content: str) -> Optional[str]:
    """
    Извлекает первый заголовок первого уровня из Markdown-контента.
    
    Возвращает текст заголовка без символа # или None, если заголовок не найден.
    """
    match = HEADING_PATTERN.search(content)
    if match:
        return match.group(1).strip()
    return None


def generate_anchor(heading: str) -> str:
    """
    Генерирует якорь для ссылки в оглавлении.
    
    Преобразует заголовок в формат, совместимый с GitHub Markdown:
    - Приводит к нижнему регистру
    - Заменяет пробелы на дефисы
    - Удаляет специальные символы (кроме дефисов и подчёркиваний)
    """
    # Приводим к нижнему регистру
    anchor = heading.lower()
    # Заменяем пробелы на дефисы
    anchor = anchor.replace(' ', '-')
    # Удаляем специальные символы, оставляем буквы, цифры, дефисы, подчёркивания
    anchor = re.sub(r'[^\w\-]', '', anchor, flags=re.UNICODE)
    # Убираем множественные дефисы
    anchor = re.sub(r'-+', '-', anchor)
    # Убираем дефисы в начале и конце
    anchor = anchor.strip('-')
    return anchor


def build_toc(files: List[Tuple[int, Path]]) -> str:
    """
    Генерирует оглавление (Table of Contents) на основе заголовков файлов.
    
    Возвращает строку с Markdown-списком ссылок на разделы.
    """
    toc_lines = ["## Оглавление", ""]
    
    for _, file_path in files:
        content = file_path.read_text(encoding='utf-8')
        heading = extract_first_heading(content)
        
        if heading:
            anchor = generate_anchor(heading)
            toc_lines.append(f"- [{heading}](#{anchor})")
        else:
            # Если заголовок не найден, используем имя файла
            name = file_path.stem
            toc_lines.append(f"- [{name}](#{name})")
    
    toc_lines.append("")  # Пустая строка в конце
    return '\n'.join(toc_lines)


def build_spec(files: List[Tuple[int, Path]]) -> str:
    """
    Собирает полную спецификацию из частей.
    
    Возвращает строку с полным содержимым SPEC.md.
    """
    # Заголовок документа
    header = [
        "<!-- Этот файл сгенерирован автоматически. Не редактируйте вручную! -->",
        "<!-- Для изменений редактируйте файлы в spec/ и запустите: python tools/build_spec.py -->",
        "",
    ]
    
    # Генерируем оглавление
    toc = build_toc(files)
    
    # Собираем содержимое всех файлов
    sections = []
    for _, file_path in files:
        content = file_path.read_text(encoding='utf-8').strip()
        sections.append(content)
    
    # Объединяем всё вместе
    parts = header + [toc] + ['\n\n---\n\n'.join(sections)]
    return '\n'.join(parts)


def main():
    """Главная функция скрипта."""
    parser = argparse.ArgumentParser(
        description='Сборка спецификации из частей в единый SPEC.md'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Проверить актуальность SPEC.md без перезаписи'
    )
    args = parser.parse_args()
    
    spec_dir = get_spec_dir()
    output_path = get_output_path()
    
    # Проверяем существование директории spec/
    if not spec_dir.exists():
        print(f"Ошибка: директория '{spec_dir}' не найдена", file=sys.stderr)
        sys.exit(1)
    
    # Находим файлы спецификации
    files = find_spec_files(spec_dir)
    
    if not files:
        print(f"Ошибка: в директории '{spec_dir}' не найдено файлов спецификации",
              file=sys.stderr)
        sys.exit(1)
    
    print(f"Найдено {len(files)} файлов спецификации:")
    for prefix, file_path in files:
        print(f"  {prefix:02d}: {file_path.name}")
    
    # Собираем спецификацию
    spec_content = build_spec(files)
    
    if args.check:
        # Режим проверки: сравниваем с существующим файлом
        if not output_path.exists():
            print(f"\nОшибка: файл '{output_path}' не существует", file=sys.stderr)
            print("Запустите 'python tools/build_spec.py' для генерации", file=sys.stderr)
            sys.exit(1)
        
        existing_content = output_path.read_text(encoding='utf-8')
        
        if existing_content == spec_content:
            print(f"\n✓ Файл '{output_path.name}' актуален")
            sys.exit(0)
        else:
            print(f"\n✗ Файл '{output_path.name}' устарел", file=sys.stderr)
            print("Запустите 'python tools/build_spec.py' для обновления", file=sys.stderr)
            sys.exit(1)
    else:
        # Режим генерации: записываем файл
        try:
            output_path.write_text(spec_content, encoding='utf-8')
            print(f"\n✓ Сгенерирован файл '{output_path}'")
        except PermissionError:
            print(f"\nОшибка: нет прав на запись в '{output_path}'", file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            print(f"\nОшибка записи файла: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
