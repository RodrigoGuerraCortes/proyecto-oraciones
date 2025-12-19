# generator/cli/publish_instagram.py

import sys
from generator.publisher.instagram import InstagramPublisher


def main():
    dry_run = "--dry-run" in sys.argv
    force_now = "--force-now" in sys.argv

    InstagramPublisher().run(
        dry_run=dry_run,
        preview_days=None,
        force_now=force_now,
    )


if __name__ == "__main__":
    main()
