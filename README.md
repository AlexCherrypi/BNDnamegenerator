# BNDnamegenerator

[![Deploy BNDnamegenerator](https://github.com/AlexCherrypi/BNDnamegenerator/actions/workflows/deploy.yml/badge.svg)](https://github.com/AlexCherrypi/BNDnamegenerator/actions/workflows/deploy.yml) [![CC BY-SA 4.0][cc-by-sa-shield]][cc-by-sa]

You might remember the old [nsanamegenerator.com](https://web.archive.org/web/20160318190656/http://www.nsanamegenerator.com/). 
In homage to that page I firstly created [alexcherrypi.github.io/nsanamegenerator/](https://alexcherrypi.github.io/nsanamegenerator/). 

But then I really wanted to create one in the mothertongue of my girlfried, because she sometimes just doesn't get the joke.

By using the underlying data of [https://github.com/hdaSprachtechnologie/odenet/](https://github.com/hdaSprachtechnologie/odenet) I created this random word generator.

[alexcherrypi.github.io/BNDnamegenerator/](https://alexcherrypi.github.io/BNDnamegenerator/) behaves like the OG version of [alexcherrypi.github.io/nsanamegenerator/og/](https://alexcherrypi.github.io/nsanamegenerator/og/) that combines two nouns, in all caps and witout any space to seperate the words.

Unlike English, German often puts a linking element (Fugenelement) between the nouns of a compound: Sonne + Blume becomes Sonne**n**blume, Zeitung + Papier becomes Zeitung**s**papier and Schule + Bus becomes Schulbus. [fugen.py](fugen.py) picks the linking element for the first word, mostly by looking at how the word is used in the compounds of the dictionary itself.

Like the real codenames, the names are made of well known words: two nouns of different kinds, like an animal and a food or a thing.

If that is too tame, two settings in the URL make the names ruder or nerdier. They can be combined, like [?vulgar=3&nerd=3](https://alexcherrypi.github.io/BNDnamegenerator/?vulgar=3&nerd=3):

| | crude words | obscure words |
|---|---|---|
| sometimes | [?vulgar](https://alexcherrypi.github.io/BNDnamegenerator/?vulgar) | [?nerd](https://alexcherrypi.github.io/BNDnamegenerator/?nerd) |
| at least one per name | [?vulgar=2](https://alexcherrypi.github.io/BNDnamegenerator/?vulgar=2) | [?nerd=2](https://alexcherrypi.github.io/BNDnamegenerator/?nerd=2) |
| nothing else | [?vulgar=3](https://alexcherrypi.github.io/BNDnamegenerator/?vulgar=3) | [?nerd=3](https://alexcherrypi.github.io/BNDnamegenerator/?nerd=3) |

Slurs never show up, not even with ?vulgar=3, and neither do words for groups of people by origin, religion or sexual orientation, words about the Nazis or abuse, or slurs made of two harmless words (Schlitz + Auge): the page simply picks again.

This is just a little side project of mine, so don't expect regular updates and a lot of ongoing development.

But if you want to suggest any features or ideas, submit them by creating an issue. I don't have any templates set up yet (and maybe never will), but don't be scared by thaat. Just write your idea down and submit the issue. :-)


## Word lists

The whole dictionary is available as word lists at `words/<list>/<number>.txt`, with the number of words in `words/<list>/len.txt`. The name of a list says what is in it, e.g. `nsgu`:

| Letter | Meaning |
|--------|---------|
| `n` / `v` / `a` / `r` | noun / verb / adjective / adverb |
| `s` / `c` | single word / combined words |
| `g` / `d` | no dash / dash |
| `l` / `u` | lower case / upper case letters |

`bestimmungswort` holds the nouns as first part of a compound, with their linking element (Sonnen, Zeitungs, Schul).

Every list also comes with extra lists sorted from the best known to the most obscure word (see [wordinfo.py](wordinfo.py)): one per category of the word's meanings, like `nsgu-animal`, `nsgu-food` or `bestimmungswort-person`, and `nsgu-vulgar` for crude words. Words that should not be shown from a list come last, after the number of words in `usable.txt`: slurs and plurals, and crude words except in the vulgar lists. `words/blocked.txt` holds short hashes of the slurs two harmless words can make up.

[![CC BY-SA 4.0][cc-by-sa-image]][cc-by-sa]

[cc-by-sa]: http://creativecommons.org/licenses/by-sa/4.0/
[cc-by-sa-image]: https://licensebuttons.net/l/by-sa/4.0/88x31.png
[cc-by-sa-shield]: https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg
[BNDnamegenerator](https://github.com/AlexCherrypi/BNDnamegenerator/) © 2023 by [AlexCherrypi](https://github.com/AlexCherrypi/) is licensed under [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/?ref=chooser-v1)

