import signal
import sys

from board import BoardDrawer
from game import Game


def main():
  Game().run()


def signal_handler(_signal, _frame):
  sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
  main()
