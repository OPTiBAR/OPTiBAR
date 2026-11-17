// Furo has no right-to-left support: lay the page out right to left before it is drawn.
// Added to the pages of right-to-left languages only (see conf.py).
document.documentElement.setAttribute('dir', 'rtl');
