Introduction
============

This file describe how to contribute and some stuff util for developers and
contributor on ig-Trace (alias L3 or L3-scalping).

Note about personal.py
----------------------

The file personal.py save your personal information like login/password for IG.
It is important to not distribute it and not commit it.

Coding style
============

All Python files that you commit must be compliant with PEP8 and PEP257. 
You can found information about it on those links:
 - https://www.python.org/dev/peps/pep-0008/
 - https://www.python.org/dev/peps/pep-0257/

Your code editor can help you to do that. Some editors are amazing about that
like :
 - VIM (with a good config)
 - EMACS (with a good config)
 - PyCharm
 - SublimeText
 - Atom

But you can use to editor of your chose.

Before commit you can also use the pep8 CLI to check if your file is 
pep8 compliant.

You can install pep8:

```bash
$ pip install pep8
```

You can also configure your editor to run pep8 and alert you when you write a
line not pep8 compliance.

Contributions
=============

If you want to contribute you can:
 - fork the upstream repo : https://github.com/splanquart/igtrade
 - commit & push your modifications on your repo
 - make a pull request to the upstream repo

For clarification and some recommandation : 
 - **local repository**: the cloned repository that you have one on your machine
 - **forked repository**: the fork you made from the main repository. This sits up
 on github’s servers. (Also known as “**origin**”)
 - **main repository**: the original repository that you forked from. This is the
 common ms-iot repository hosted on github’s servers. (Also known as “**upstream**”)
 - all you pull requests must be automergable (understand : without conflict)
 - if you want make more than one features, create multiple pull requests (one
 by features)
