# cli/publish_tiktok.py

import sys
from generator.publisher.tiktok import TikTokPublisher


def main():
    dry_run = "--dry-run" in sys.argv
    force_now = "--force-now" in sys.argv

    TikTokPublisher().run(
        dry_run=dry_run,
        force_now=force_now,
    )


if __name__ == "__main__":
    main()
