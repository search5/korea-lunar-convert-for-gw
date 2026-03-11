#!/usr/bin/env python3
"""
마크다운 파일에 Jekyll front matter를 추가하는 스크립트.

사용법:
  python3 add_frontmatter.py privacy.md
  python3 add_frontmatter.py terms.md --title "이용약관" --permalink /terms/
  python3 add_frontmatter.py *.md           # 여러 파일 일괄 처리

옵션:
  --title TEXT        페이지 제목 (생략 시 파일명에서 자동 추출)
  --permalink TEXT    URL 경로 (생략 시 /파일명/ 으로 자동 설정)
  --layout TEXT       레이아웃 이름 (기본값: default)
  --overwrite         이미 front matter가 있어도 덮어씀
  --dry-run           실제 파일을 수정하지 않고 결과만 출력
"""

import argparse
import re
import sys
from pathlib import Path

# 파일명 → 제목 매핑 (없으면 파일명을 그대로 사용)
TITLE_MAP = {
    "privacy":       "개인정보처리방침",
    "terms":         "서비스 이용약관",
    "support":       "지원",
    "index":         "음력 변환기",
}

# 파일명 → permalink 매핑 (없으면 /파일명/ 사용, index는 /)
PERMALINK_MAP = {
    "index":   "/",
    "privacy": "/privacy/",
    "terms":   "/terms/",
    "support": "/support/",
}

FRONT_MATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def has_front_matter(text: str) -> bool:
    return text.startswith("---\n") or text.startswith("---\r\n")


def extract_h1_title(text: str) -> str | None:
    """파일 내 첫 번째 # 제목 추출"""
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def build_front_matter(title: str, permalink: str, layout: str) -> str:
    return f"---\ntitle: {title}\npermalink: {permalink}\nlayout: {layout}\n---\n\n"


def process_file(path: Path, title: str | None, permalink: str | None,
                 layout: str, overwrite: bool, dry_run: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    stem = path.stem.lower()

    if has_front_matter(text):
        if not overwrite:
            print(f"  ⏭  {path.name} — front matter 이미 존재 (--overwrite 로 덮어쓸 수 있음)")
            return False
        # 기존 front matter 제거
        text = FRONT_MATTER_RE.sub("", text, count=1)

    resolved_title = title or TITLE_MAP.get(stem) or extract_h1_title(text) or stem
    resolved_permalink = permalink or PERMALINK_MAP.get(stem) or f"/{stem}/"

    new_text = build_front_matter(resolved_title, resolved_permalink, layout) + text

    if dry_run:
        print(f"  🔍 {path.name} (dry-run)")
        print(f"     title: {resolved_title}")
        print(f"     permalink: {resolved_permalink}")
    else:
        path.write_text(new_text, encoding="utf-8")
        print(f"  ✅ {path.name} → permalink: {resolved_permalink}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="마크다운 파일에 Jekyll front matter 추가"
    )
    parser.add_argument("files", nargs="+", help="처리할 .md 파일 (글로브 가능)")
    parser.add_argument("--title",     help="페이지 제목 (단일 파일 처리 시)")
    parser.add_argument("--permalink", help="URL 경로 (단일 파일 처리 시)")
    parser.add_argument("--layout",    default="default", help="레이아웃 (기본: default)")
    parser.add_argument("--overwrite", action="store_true", help="기존 front matter 덮어쓰기")
    parser.add_argument("--dry-run",   action="store_true", help="실제 수정 없이 미리보기")
    args = parser.parse_args()

    paths = []
    for pattern in args.files:
        matched = list(Path(".").glob(pattern)) or [Path(pattern)]
        paths.extend(p for p in matched if p.suffix == ".md" and p.exists())

    if not paths:
        print("처리할 .md 파일을 찾을 수 없습니다.", file=sys.stderr)
        sys.exit(1)

    # 단일 파일일 때만 --title, --permalink 수동 지정 허용
    if len(paths) > 1 and (args.title or args.permalink):
        print("⚠️  --title, --permalink 는 단일 파일 처리 시에만 사용할 수 있습니다.",
              file=sys.stderr)
        sys.exit(1)

    print(f"{'[dry-run] ' if args.dry_run else ''}파일 {len(paths)}개 처리 중...\n")
    changed = 0
    for p in paths:
        if process_file(p, args.title, args.permalink,
                        args.layout, args.overwrite, args.dry_run):
            changed += 1

    print(f"\n완료: {changed}/{len(paths)}개 파일 {'업데이트 예정' if args.dry_run else '업데이트됨'}")


if __name__ == "__main__":
    main()
