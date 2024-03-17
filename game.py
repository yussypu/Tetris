import curses
import datetime
import math
import sys

from board import Board, BoardDrawer, GameOverError


class Game(object):
  '''Manages the game and updating the screen.'''

  def __init__(self):
    '''Initializes a new game.'''

    self.last_tick = None
    self.board = Board(columns=10, rows=20)
    self.board_drawer = self.board.drawer
    self.board_drawer.clear_score()
    self.board.start_game()
    self.tick_length = 600

  def pause(self):
    '''Pauses or unpauses the game.'''

    if self.last_tick:
      self.stop_ticking()
    else:
      self.start_ticking()

  def run(self):
    '''Kicks off the game event loop.'''

    self.start_ticking()
    self._tick()

    while True:
      try:
        self.process_user_input()
        self.update()
      except GameOverError:
        self.end()
        return self.board.score

  # @TODO: Fix this
  def end(self):
    '''Ends the game.'''

    self.exit()

  def exit(self):
    '''Exits the program.'''

    curses.endwin()
    print('Game Over! Final Score: {}'.format(int(self.board.score)))
    sys.exit(0)

  def start_ticking(self):
    self.last_tick = datetime.datetime.now()

  def stop_ticking(self):
    self.last_tick = None

  def update(self):
    current_time = datetime.datetime.now()
    tick_multiplier = math.pow(0.9, self.board.level - 1)
    tick_threshold = datetime.timedelta(milliseconds=self.tick_length *
                                        tick_multiplier)

    if self.last_tick and current_time - self.last_tick > tick_threshold:
      self.last_tick = current_time
      self._tick()

  def _tick(self):
    self.board.let_shape_fall()
    self.board_drawer.update(self.board)

  def process_user_input(self):
    user_input = self.board_drawer.stdscr.getch()
    moves = {
        curses.KEY_RIGHT: self.board.move_shape_right,
        curses.KEY_LEFT: self.board.move_shape_left,
        curses.KEY_UP: self.board.rotate_shape,
        curses.KEY_DOWN: self.board.let_shape_fall,
        curses.KEY_ENTER: self.board.drop_shape,
        10: self.board.drop_shape,
        13: self.board.drop_shape,
        112: self.pause,
        113: self.exit,
    }
    move_fn = moves.get(user_input)
    if move_fn:
      piece_moved = move_fn()
      if piece_moved:
        self.board_drawer.update(self.board)
