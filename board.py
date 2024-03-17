import copy
import curses
import math

from pieces import Shape


class Board(object):
  '''Maintains the entire state of the game.'''

  def __init__(self, columns=None, rows=None, level=None):
    self.num_rows = rows
    self.num_columns = columns
    self.array = [[None for _ in range(self.num_columns)]
                  for _ in range(self.num_rows)]
    self.falling_shape = None
    self.next_shape = None
    self.score = 0
    self.level = level or 1
    self.preview_column = 12
    self.preview_row = 1
    self.starting_column = 4
    self.starting_row = 0
    self.drawer = BoardDrawer(self)
    self.points_per_line = 20
    self.points_per_level = 200

  def start_game(self):
    self.score = 0
    self.level = 1
    if self.next_shape is None:
      self.next_shape = Shape.random(self.preview_column, self.preview_row)
      self.new_shape()

  def end_game(self):
    raise GameOverError(score=self.score, level=self.level)

  def new_shape(self):
    self.falling_shape = self.next_shape
    self.falling_shape.move_to(self.starting_column, self.starting_row)
    self.next_shape = Shape.random(self.preview_column, self.preview_row)
    if self.shape_cannot_be_placed(self.falling_shape):
      self.next_shape = self.falling_shape
      self.falling_shape = None
      self.next_shape.move_to(self.preview_column, self.preview_row)
      self.end_game()

  def remove_completed_lines(self):
    rows_removed = []
    lowest_row_removed = 0
    for row in self.array:
      if all(row):
        lowest_row_removed = max(lowest_row_removed, row[0].row_position)
        rows_removed.append(copy.deepcopy(row))
        for block in row:
          self.array[block.row_position][block.column_position] = None
    if len(rows_removed) > 0:
      points_earned = math.pow(2, len(rows_removed) - 1) * self.points_per_line
      self.score += points_earned
      if self.score > self.points_per_level * self.level:
        self.level += 1

      for column_index in range(0, self.num_columns):
        for row_index in range(lowest_row_removed, 0, -1):
          block = self.array[row_index][column_index]
          if block:
            # Number of rows removed that were below this one
            distance_to_drop = len([
                row for row in rows_removed
                if row[0].row_position > block.row_position
            ])
            new_row_index = row_index + distance_to_drop
            self.array[row_index][column_index] = None
            self.array[new_row_index][column_index] = block
            block.row_position = new_row_index

  def settle_falling_shape(self):
    '''Resolves the current falling shape.'''

    if self.falling_shape:
      self._settle_shape(self.falling_shape)
      self.falling_shape = None
      self.new_shape()

  def _settle_shape(self, shape):
    '''Adds shape to settled pieces array.'''

    if shape:
      for block in shape.blocks:
        self.array[block.row_position][block.column_position] = block
    self.remove_completed_lines()

  def move_shape_left(self):
    if self.falling_shape:
      self.falling_shape.shift_shape_left_by_one_column()
      if self.shape_cannot_be_placed(self.falling_shape):
        self.falling_shape.shift_shape_right_by_one_column()
        return False
      return True

  def move_shape_right(self):
    if self.falling_shape:
      self.falling_shape.shift_shape_right_by_one_column()
      if self.shape_cannot_be_placed(self.falling_shape):
        self.falling_shape.shift_shape_left_by_one_column()
        return False
      return True

  def rotate_shape(self):
    if self.falling_shape:
      self.falling_shape.rotate_clockwise()
      if self.shape_cannot_be_placed(self.falling_shape):
        self.falling_shape.rotate_counterclockwise()
        return False
      return True

  def let_shape_fall(self):
    '''What happens during every `tick`. Also what happens when the user hits down arrow.'''

    if self.falling_shape:
      self.falling_shape.lower_shape_by_one_row()
      if self.shape_cannot_be_placed(self.falling_shape):
        self.falling_shape.raise_shape_by_one_row()
        if self.shape_cannot_be_placed(self.falling_shape):
          self.end_game()
        else:
          self.settle_falling_shape()
      return True

  def drop_shape(self):
    '''When you hit the enter arrow and the piece goes all the way down.'''

    if self.falling_shape:
      while not self.shape_cannot_be_placed(self.falling_shape):
        self.falling_shape.lower_shape_by_one_row()
      self.falling_shape.raise_shape_by_one_row()
      if self.shape_cannot_be_placed(self.falling_shape):
        self.end_game()
      else:
        self.settle_falling_shape()
      return True

  def shape_cannot_be_placed(self, shape):
    '''Determines whether a shape can successfully be placed.'''

    for block in shape.blocks:
      if (block.column_position < 0
          or block.column_position >= self.num_columns
          or block.row_position < 0 or block.row_position >= self.num_rows or
          self.array[block.row_position][block.column_position] is not None):
        return True
    return False


class BoardDrawer(object):
  '''Manages drawing the board.'''

  def __init__(self, board):
    stdscr = curses.initscr()
    stdscr.nodelay(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_RED)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLUE)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_GREEN)
    curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_CYAN)
    curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_YELLOW)
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(10, 10, 10)
    curses.cbreak()
    stdscr.keypad(1)
    curses.nonl()
    curses.curs_set(0)
    curses.noecho()
    self.stdscr = stdscr
    self.preview_column = board.preview_column
    self.preview_row = board.preview_row
    self.num_rows = board.num_rows
    self.num_columns = board.num_columns
    self.block_width = 2
    self.border_width = 1

  def update_falling_piece(self, board):
    '''Adds the currently falling pieces to the next stdscr to be drawn.'''

    if board.falling_shape:
      for block in board.falling_shape.blocks:
        self.stdscr.addstr(
            block.row_position + self.border_width,
            self.block_width * block.column_position + self.border_width,
            ' ' * self.block_width, curses.color_pair(block.color))

  def update_settled_pieces(self, board):
    '''Adds the already settled pieces to the next stdscr to be drawn.'''

    for (r_index, row) in enumerate(board.array):
      for (c_index, value) in enumerate(row):
        block = value
        if block:
          color_pair = block.color
        else:
          color_pair = 0
        self.stdscr.addstr(r_index + self.border_width,
                           c_index * self.block_width + self.border_width,
                           ' ' * self.block_width,
                           curses.color_pair(color_pair))

  def update_shadow(self, board):
    '''Adds the 'shadow' of the falling piece to the next stdscr to be drawn.'''

    # Projects a shadow of where the piece will land.
    shadow = copy.deepcopy(board.falling_shape)
    if shadow:
      while not board.shape_cannot_be_placed(shadow):
        shadow.lower_shape_by_one_row()
      shadow.raise_shape_by_one_row()
      for block in shadow.blocks:
        self.stdscr.addstr(
            block.row_position + self.border_width,
            self.block_width * block.column_position + self.border_width,
            ' ' * self.block_width, curses.color_pair(8))

  def update_next_piece(self, board):
    '''Adds the next piece to the next stdscr to be drawn.'''

    if board.next_shape:
      for preview_row_offset in range(4):
        self.stdscr.addstr(
            self.preview_row + preview_row_offset + self.border_width,
            (self.preview_column - 1) * self.block_width +
            self.border_width * 2, '    ' * self.block_width,
            curses.color_pair(0))
      for block in board.next_shape.blocks:
        self.stdscr.addstr(
            block.row_position + self.border_width,
            block.column_position * self.block_width + self.border_width * 2,
            ' ' * self.block_width, curses.color_pair(block.color))

  def update_score_and_level(self, board):
    '''Adds the score and level to the next stdscr to be drawn.'''

    # Level
    self.stdscr.addstr(
        5 + self.border_width,
        self.preview_column * self.block_width - 2 + self.border_width,
        'LEVEL: %d' % board.level, curses.color_pair(7))
    # Score
    self.stdscr.addstr(
        6 + self.border_width,
        self.preview_column * self.block_width - 2 + self.border_width,
        'SCORE: %d' % board.score, curses.color_pair(7))

  def clear_score(self):
    '''Does what it says on the tin.'''

    # Level
    self.stdscr.addstr(
        5 + self.border_width,
        self.preview_column * self.block_width - 2 + self.border_width,
        'LEVEL:              ', curses.color_pair(7))
    # Score
    self.stdscr.addstr(
        6 + self.border_width,
        self.preview_column * self.block_width - 2 + self.border_width,
        'SCORE:              ', curses.color_pair(7))

  def update_border(self):
    '''Adds the border to the next stdscr to be drawn.'''

    # Side borders
    for row_position in range(self.num_rows + self.border_width * 2):
      if row_position < curses.LINES:  # Check if within screen boundaries
        self.stdscr.addstr(row_position, 0, '|', curses.color_pair(7))
        self.stdscr.addstr(row_position,
                           self.num_columns * self.block_width + 1, '|',
                           curses.color_pair(7))

    # Top and bottom borders
    for column_position in range(self.num_columns * self.block_width +
                                 self.border_width * 2):
      if column_position < curses.COLS:  # Check if within screen boundaries
        self.stdscr.addstr(0, column_position, '-', curses.color_pair(7))
        self.stdscr.addstr(self.num_rows + 1, column_position, '-',
                           curses.color_pair(7))

  def update(self, board):
    '''Updates all visual board elements and then refreshes the screen.'''

    self.update_border()
    self.update_score_and_level(board)
    self.update_next_piece(board)
    self.update_settled_pieces(board)
    self.update_falling_piece(board)
    self.update_shadow(board)
    self.refresh_screen()

  def refresh_screen(self):
    stdscr = self.stdscr
    stdscr.refresh()


class GameOverError(Exception):

  def __init__(self, score, level):
    super(GameOverError).__init__(GameOverError)
    self.score = score
    self.level = level
