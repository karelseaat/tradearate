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

    transcont = {}
    defaulttranscont = {}

    def __init__(self, localename=None):

        if localename:
            if not os.path.exists("./trans-{}.toml".format(localename)):
                open("./trans-{}.toml".format(localename), "x").close()

            self.transfile = open("./trans-{}.toml".format(localename), "r+")

            if self.transfile:
                cont = self.transfile.read()
                self.transcont =  toml.loads(cont, _dict=dict)

        if not os.path.exists("./trans-default.toml"):
            open("./trans-default.toml", "x").close()

        self.defaulttransfile = open("./trans-default.toml", "r+")

        if self.defaulttransfile:
            cont = self.defaulttransfile.read()
            self.defaulttranscont =  toml.loads(cont, _dict=dict)

    def trans(self, word):

        if word in self.transcont:
            return self.transcont[word]
        else:
            self.defaulttranscont.update({word: word})
            return word

    def close(self):
        self.transfile.seek(0, 0)
        self.defaulttransfile.seek(0, 0)

        self.transfile.write(toml.dumps(self.transcont))
        self.defaulttransfile.write(toml.dumps(self.defaulttranscont))

        self.transfile.close()
        self.defaulttransfile.close()


if __name__ == "__main__":
    pyn = PyNalator("nl")
    print(pyn.trans("test"))
    print(pyn.trans("aap"))
    print(pyn.trans("faaaack"))
    print(pyn.trans("nog test"))
    pyn.trans("iets")

    pyn.close()
