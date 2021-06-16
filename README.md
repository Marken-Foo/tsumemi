# Tsumemi 詰め見 - KIF browser #

Navigate through your tsumeshogi problems with ease. Speedrun a set of tsumeshogi problems and record and save your statistics.

![](browser.png)

Shogi players may have hundreds of tsumeshogi stored in .kif files. For stronger players who can solve each problem at a glance, the total time taken opening each file in turn can be many times longer than the actual solving.

Tsumemi lets shogi players train with their large collections of tsumeshogi quickly and efficiently.

Comes with a free set of ten 1-te and ten 3-te problems in the folder `/sample_problems`, composed by Marken Foo.

## How to install ##

### Zip file ###

Windows 10 users can download a zip file from the [Releases](https://github.com/Marken-Foo/tsumemi/releases/) tab.

To use, unzip the folder somewhere and run the `tsumemi.exe` executable file inside.

### From source ###

Dependencies: Python 3.7 (tested with 3.8.1) or later, TKinter 8.6 or later, Pillow (tested with 8.1.0)

Download the repo into the working directory of your choice, e.g. `git svn clone https://github.com/Marken-Foo/tsumemi/trunk` (Git SVN) or `git clone https://github.com/Marken-Foo/tsumemi.git` (Git).

To run, either run `tsumemi_launcher.py` (make sure it's in the same directory as the top-level tsumemi folder), or run the tsumemi top-level package from the command line with `python3 -m tsumemi`.

### From source (for the less technically-inclined) ###

You'll need Python 3, which will help you run Python (.py) code files on your computer. You can download an installer for the latest version from the [official Python website](https://www.python.org/). It also comes with TKinter.

You'll also need Pillow, which lets Python files deal with images. Once you've installed Python (let it change your PATH variable when installing!), open a console (Command Prompt, Windows Powershell, Mac Terminal, bash, etc). Type `pip install Pillow` and press Enter. This should install Pillow.

(If you have issues with the above steps, you can consult the first two sections of some [documentation on how to install python packages](https://packaging.python.org/tutorials/installing-packages/).

Download everything in this GitHub repository. You can go to the [main page of this repository](https://github.com/Marken-Foo/tsumemi), click the green "Code" at the top right of the file list, and you can download everything as a zip file.

Finally, to run the program, double click on `tsumemi_launcher.py`.

## How to use ##

From the menu bar, "File -> Open folder...", or Ctrl-O opens the folder selection dialog. Select a folder, and all kifu files within the folder will be opened.

### Free mode ###

The board position of the first kifu file will be shown once you open a folder. Click "Show/hide solution" or press H to show or hide the solution (it must be entered as the main line in the kifu file).

Press "< Prev" (or the left arrow key) or "Next >" (or the right arrow key) to go to the previous or next .kif files in the selected directory.

Check "Upside-down mode" to display the positions from gote's point of view instead, for a different style of training.

There is a simple stopwatch under the problem list. "Split" records the time taken to solve the current problem (time since the last split).

### Speedrun mode ###

The "Start speedrun" button will enter **speedrun mode**, where you can go through all the problems in the folder in order while your times for solving each are recorded.

For each problem, you can move pieces to solve it. Illegal moves will be ignored (except uchifuzume/pawn-drop mate), but any wrong move will be flagged as a wrong answer.

Alternatively, *Show solution* lets you check your answer and choose whether you got it right or wrong (the timer will be paused while doing so). If you cannot solve the problem, you can *Skip* to the next problem without seeing the solution.

Your time splits and correct/wrong/skip/unattempted status for each problem are displayed in the panel on the right.

### Speedrun statistics ###

From the Speedrun menu, you can get your solving statistics on the current problem set, export them as a CSV file, or clear your current statistics.

### Customise appearance ###

Go to "Settings > Settings..." and a window will pop up, allowing you to choose the piece and board graphics you like. Included are several sets of [boards and pieces by Ka-hu](https://github.com/Ka-hu/shogi-pieces/).

Internationalised pieces are included.

## Feedback ##

If you encounter any bugs, let me know. Do include steps of what you were doing to trigger the bug, examples of .kif files that couldn't be read, or even screenshots if they help.

## Licence ##

This project originally written by [Marken Foo](https://github.com/Marken-Foo/) and is **licensed under the GPLv3**.

The following boards and pieces by [Ka-hu](https://github.com/Ka-hu/shogi-pieces/), **licensed under CC-BY-4.0**.

- Boards: tile_wood1 through to tile_wood6, tile_stone, tile_military and tile_military2
- Pieces: kanji_light, kanji_brown, kanji_red and international

The following piece sets by [CouchTomato87](https://github.com/CouchTomato87), **licensed under CC-BY-4.0**.

- Pieces: tomato_colored, tomato_monochrome