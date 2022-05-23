import threading

from omg_scotus.fetcher import Stream
from omg_scotus.website_change_detector import ChangeDetector


def main() -> int:
    cd1 = ChangeDetector(stream=Stream.SLIP_OPINIONS)
    cd2 = ChangeDetector(stream=Stream.OPINIONS_RELATING_TO_ORDERS)
    cd3 = ChangeDetector(stream=Stream.ORDERS)

    thread1 = threading.Thread(target=cd1.start_detection)
    thread2 = threading.Thread(target=cd2.start_detection)
    thread3 = threading.Thread(target=cd3.start_detection)

    thread1.start()
    thread2.start()
    thread3.start()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
