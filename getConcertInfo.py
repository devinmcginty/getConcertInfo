#!/usr/bin/python
"""
    Program:    getConcertInfo.py
    Author:     Devin McGinty

    This pulls information from the WXPN concert calendar and displays it
    using in two windows (using ncurses). The left window displays the list of
    artists and the right window displays artist concert information.

    Uses:
        curses
        locale
        re
        urllib
"""

__author__ = "Devin McGinty"

import curses
import locale
import re
# import sys
from urllib import urlopen

def getMonth(n):
    """Return a month name for a given integer n."""
    months = ["January", "February", "March", "April",
                  "May", "June", "July", "August",
                  "September", "October", "November", "December"]
    return months[(int(n) - 1) % 12]

def formatConcert(day,date,venue,cost):
    """Pack concert information into a dictionary"""
    date = date.split('-')
    m, d, y = range(3)  # MM-DD-YYYY formatted day
    details = ["venue", "year", "month", "date", "day", "cost"]
    concert = [venue, date[y], date[m], date[d], day, cost]
    return dict(zip(details, concert))

def concertList(url):
    """Pull WXPN concert calendar to parse concert data.
    Return a library, with artist names as keys, corresponding to lists of
    libraries, each representing a concert. The structure is formatted below:

    { "Artist name":
        [
            { Concert 1 Library },
            { Concert 2 Library } ...
        ], ...
    }

    Requires:
        urllib.urlopen
        re
    Calls:
        formatConcert()
    """
    site = urlopen(url)
    site_data = site.readlines()
    site.close()
#   All concert information is denoted with table cell tags
    artist_tag = "<td "
    site_data = [l for l in site_data if artist_tag in l]
#   Regex's for components to parse
    artist_re = re.compile("(?<=<b>)[^<]+(?=<)")
    day_re = re.compile('(?<=-1">)[a-zA-Z]{3}(?=<)')
    date_re = re.compile('(?<=0">)[0-9\-]{10}')
    venue_re = re.compile('(?<=2">)[^<]*')
    cost_re = re.compile('(?<=3">)[^<]*')
    artists = {}
    for l in site_data:
        art = artist_re.search(l)
        if art:
            name = art.group()
            day = day_re.search(l).group()
            date = date_re.search(l).group()
            venue = venue_re.search(l).group()
            cost = cost_re.search(l).group()
            concert = formatConcert(day,date,venue,cost)
            if name not in artists:
                artists[name] = [concert]
            else:
                artists[name].append(concert)
    return artists

def trimName(name,length):
    """Trim a string and append an ellipses (...) if the string exceeds a
    given length.
    """
    if len(name) > length:
        name = name[:length] + "..."
    return name

def populateListWin(win, names, offset, MID_Y, width):
    """Populate the artist list window. The active artist, given by names[offset]
    is highlighted and indented, in order to make it stand out, as shown:

     ____________________
    |names[offset - 2]   |
    |names[offset - 1]   |
    |  NAMES[offset]     |
    |names[offset + 1]   |
    |names[offset + 2]   |
    |____________________|

    Parameters:
        win - Curses subwindow to be populated
        names - List of alphabetized artist names
        offset - Name to be highlighted
        MID_Y - vertical midpoint of win, position of names[offset]
        width - horizontal width of window, used to trim strings to fit

    Requires:
        curses
    Calls:
        trimName()
    """
    win.clear()
    win.border()
    MARGIN = 1
    width -= 7
    SHIFT = 4
    main_name = trimName(names[offset], width - SHIFT)
#   Add highlighted name
    win.addstr(MID_Y, MARGIN + SHIFT, main_name, curses.A_STANDOUT)
#   Add other names
    for row in range(1, MID_Y - MARGIN):
        if offset - row >= 0:           #   Above midpoint
            artist = trimName(names[offset - row], width)
            win.addstr(MID_Y - row, MARGIN, artist)
        if offset + row < len(names):   #   Below midpoint
            artist = trimName(names[offset + row], width)
            win.addstr(MID_Y + row, MARGIN, artist)
    win.refresh()

def populateInfoWin(win, concerts, name):
    """Populate info window with artist and concert information.

    Parameters:
        win - curses subwindow to be populated
        concerts - List of dictionaries, each dictionary repesents a concert.
        name - Artist name

    Requires:
        curses
    """
    win.clear()
    win.border()
    MARGIN = 4
    win.addstr(MARGIN / 2, MARGIN / 2, name, curses.A_UNDERLINE)
    row = MARGIN
    for c in concerts:
        day = c["day"] + " "
        day += c["date"] + " "
        day += getMonth(c["month"]) + " "
        day += c["year"]
        win.addstr(row, MARGIN, c["venue"], curses.A_BOLD)
        win.addstr(row + 1, MARGIN * 2, day)
        win.addstr(row + 2, MARGIN * 2, c["cost"])
        row += 4
    win.refresh()

def main(screen):
    """Initialize artist list and curses.
    Wait for user input and update subwindows accordingly, or quit.
    Requires connection to the internet to retrieve WXPN website

    Requires:
        curses
    Calls:
        concertList()
        populateInfoWin()
        populateListWin()
    """
#   Load concert data
    URL = "http://www.xpn.org/events/concert-calendar"
    concerts = concertList(URL)
#   Initialize curses
    screen.leaveok(1)
    curses.curs_set(0)
#   Set up main screen, footer information.
    MAX_Y, MAX_X = screen.getmaxyx()
    MARGIN = 2
    guide = "Scroll down/up using arrow keys or 'j'/'k'. Press 'q' to quit.\n"
    guide += "  Fast scroll using 'J'/'K'."
    screen.addstr(MAX_Y - MARGIN,MARGIN,guide)
    info = "Devin McGinty 2014"
    screen.addstr(MAX_Y - MARGIN,MAX_X - (len(info) + 2 * MARGIN),info)
#   Create sub windows
    SUB_Y = MAX_Y - (2 * MARGIN)
    SUB_X = (MAX_X / 2) - (2 * MARGIN)
    LIST_WIN = screen.subwin(SUB_Y, SUB_X, MARGIN, MARGIN)
    LIST_MID = int((LIST_WIN.getmaxyx()[0]) / 2)
    INFO_WIN = screen.subwin(SUB_Y, SUB_X , MARGIN, (2 * MARGIN + SUB_X))
    artists = list(sorted(concerts))
    offset = 0
    UP = curses.KEY_UP
    DN = curses.KEY_DOWN
#   Main loop
    while 1:
        populateListWin(LIST_WIN, artists, offset, LIST_MID, SUB_X)
        name = artists[offset]
        populateInfoWin(INFO_WIN, concerts[name], name)
        c = screen.getch()
        if c == ord('q') or c == ord('Q'):
            break
        elif (c == UP or c == ord('k')) and offset > 0:
            offset -= 1
        elif (c == DN or c == ord('j')) and offset < len(artists):
            offset += 1
        elif c == ord('K') and offset > 0:
            offset -= SUB_Y - (2 * MARGIN)
        elif c == ord('J') and offset < len(artists):
            offset += SUB_Y - (2 * MARGIN)
#       Safety resets for the offset
        if offset > len(artists) - 1:
            offset = len(artists) - 1
        if offset < 0:
            offset = 0

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL,"")
    curses.wrapper(main)

