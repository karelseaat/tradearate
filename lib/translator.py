#!/usr/bin/env python

#Wat moet het doen
#1 een kortnamige functie beschikbaar stellen om te gebruiken in de template
# toevoegen van een vertaling in de default als de vertaling aangeroepen in de vertaal functie nog niet bestaat.
# lezen van een parameter/variable die zegt van welke vertalings file er gebruikt moet worden
# inlezen van de fertalings files in de vorm van toml ?

import os
import toml
import zlib

class PyNalator:

    transfile = None
    defaulttransfile = None

    transcont = {}
    defaulttranscont = {}

    def __init__(self, localename=None, subdir="."):

        if localename:
            if not os.path.exists(f"./{subdir}/trans-{localename}.toml"):
                open(f"./{subdir}/trans-{localename}.toml", "x", encoding="utf8").close()

            self.transfile = open(f"./{subdir}/trans-{localename}.toml", "r+", encoding="utf8")

            if self.transfile:
                cont = self.transfile.read()
                self.transcont =  toml.loads(cont, _dict=dict)

        if not os.path.exists(f"./{subdir}/trans-default.toml"):
            open(f"./{subdir}/trans-default.toml", "x", encoding="utf8").close()

        self.defaulttransfile = open(f"./{subdir}/trans-default.toml", "r+", encoding="utf8")

        if self.defaulttransfile:
            cont = self.defaulttransfile.read()
            self.defaulttranscont =  toml.loads(cont, _dict=dict)

    def trans(self, word, location):
        """translate a strting if possible if not add to default translate"""

        hash = zlib.adler32(word.encode('ascii'))
        if hash in self.transcont:
            return self.transcont[hash][0]

        self.defaulttranscont.update({str(hash): (word, location._TemplateReference__context.name)})

        return word

    def close(self):
        """write all new translations and after that close all files used, it is the end of a translation cycle"""

        if self.transfile:
            self.transfile.seek(0, 0)
            self.transfile.write(toml.dumps(self.transcont))
            self.transfile.close()

        if self.defaulttransfile:
            self.defaulttransfile.seek(0, 0)
            self.defaulttransfile.write(toml.dumps(self.defaulttranscont))
            self.defaulttransfile.close()


if __name__ == "__main__":
    pyn = PyNalator("nl", subdir="../translations")
    print(pyn.trans("test", "test"))
    print(pyn.trans("aap", "test"))
    print(pyn.trans("faaaack", "test"))
    print(pyn.trans("nog test", "test"))
    pyn.trans("iets", "test")

    pyn.close()
