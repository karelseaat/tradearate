#!/usr/bin/env python

#Wat moet het doen
#1 een kortnamige functie beschikbaar stellen om te gebruiken in de template
# toevoegen van een vertaling in de default als de vertaling aangeroepen in de vertaal functie nog niet bestaat.
# lezen van een parameter/variable die zegt van welke vertalings file er gebruikt moet worden
# inlezen van de fertalings files in de vorm van toml ?

import toml
import os

class PyNalator:

    transfile = None
    defaulttransfile = None

    def __init__(self, localename=None):

        if localename:
            if not os.path.exists("./trans-{}.toml".format(localename)):
                open("./trans-{}.toml".format(localename), "x").close()

            self.transfile = "./trans-{}.toml".format(localename)

        if not os.path.exists("./trans-default.toml"):
            open("./trans-default.toml", "x").close()

        self.defaulttransfile = "./trans-default.toml"

    def trans(self, word):
        lel = {}
        if self.transfile:
            transfile = open(self.transfile, "r+")
            transfile.seek(0, 0)
            cont = transfile.read()
            lel = toml.loads(cont, _dict=dict)
            transfile.close()

        if word in lel:
            return lel[word]
        else:
            defaulttransfile = open(self.defaulttransfile, "r+")
            cont = defaulttransfile.read()
            defaulttransfile.truncate(0)
            defaulttransfile.seek(0, 0)
            lel = toml.loads(cont, _dict=dict)
            lel.update({word: word})
            defaulttransfile.write(toml.dumps(lel))
            defaulttransfile.close()
            return word



if __name__ == "__main__":
    pyn = PyNalator("nl")
    print(pyn.trans("test"))
    print(pyn.trans("aap"))
    print(pyn.trans("faaaack"))
    print(pyn.trans("nog test"))
    pyn.trans("iets")
