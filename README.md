# KIF browser #

Navigate through a folder of tsumeshogi problems with ease. For each problem, see the board position and view the solution when done solving.

![](browser.png)

Shogi players may have hundreds of tsumeshogi stored in .kif files. However, as far as I'm aware there isn't a program to quickly go through these files. For stronger players who can solve each problem at a glance, the total time taken opening each file in turn can be many times more than the actual solving.

This little bit of Python aims to let shogi players train with their large collections of tsumeshogi quickly and efficiently.

## How to install ##

[Python 3](https://www.python.org/) is required. (Tested with Python 3.8 but should be compatible with some older Python 3 versions.)

Put all the `.py` files (`board_canvas.py`, `kif_browser_gui.py`, `kif_parser.py` and `split_timer.py` in the same folder. To run, double click `kif_browser_gui.py` or run it from the command line.

## How to use ##

"File -> Open folder..." or Ctrl-O opens the folder selection dialog. Select the folder containing the tsumeshogi kifu files you want to browse.

The board position should then show. Click "Show/hide solution" or press H to show or hide the solution (it must be entered as the main line in the kifu file).

Press "< Prev" (or the left arrow key) and "Next >" (or the right arrow key) to go to the previous or next .kif files in the selected directory.

Check "Upside-down mode" to display the positions from gote's point of view instead, for a different style of training.

There is a simple stopwatch timer under the problem list. "Split" will record the time since the last split as the time taken to solve the current problem, then automatically go to the next problem.

## Feedback ##

This is just a small bit of code to try making something convenient. If you encounter any bugs, let me know. Including an example of the offending .kif files that it couldn't read would help.