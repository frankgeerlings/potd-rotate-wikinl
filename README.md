# Rotate picture of the day

This script operates on Dutch Wikipedia (with the MediaWiki API exposed through pywikibot) and copies the dutch translation of the Wikimedia Commons [Picture of the day][potd] description to a page on Dutch Wikipedia, for them to be shown on the homepage.

The script fetches all descriptions starting tomorrow up to and including the last day of the current month, and then from the first day of the next month up to and including 'yesterday + 1 month'.

Any user can run the script at any time. The script is currently scheduled to run every 15 minutes by a bot named [Geerlings' robot][frankrobot].

[frankrobot]: https://nl.wikipedia.org/wiki/Gebruiker:Geerlings%27_robot
[potd]: https://commons.wikimedia.org/wiki/Commons:Picture_of_the_day
