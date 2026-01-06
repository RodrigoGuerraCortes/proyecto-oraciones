# generator/v3/cli/publish_youtube.py

import sys
from generator.v3.publisher.youtube import YouTubePublisher


def main():
    dry_run = "--dry-run" in sys.argv

    preview_days = None
    if "--preview-2d" in sys.argv:
        preview_days = 2
    elif "--preview-1d" in sys.argv:
        preview_days = 1
    elif "--preview-5d" in sys.argv:
        preview_days = 5

    YouTubePublisher().run(
        dry_run=dry_run,
        preview_days=preview_days,
    )


if __name__ == "__main__":
    main()
