#!/usr/bin/env python

import os
import re
from numpy import *

def read_words(max_length):
    words = open('words').read().lower().split()
    keep = []
    for word in words:
        if len(word)>max_length:
            break
        keep.append(word)
    return keep

def sort_word(word):
    return ''.join(sorted(word))

max_length = 5
dictionary = dict((sort_word(w),w) for w in read_words(max_length))

def random_subset(s,n):
    r = ''
    for _ in xrange(n):
        i = random.randint(len(s))
        r += s[i]
        s = s[:i] + s[i+1:]
    return r

def subtract(a,b):
    for c in b:
        i = a.find(c)
        a = a[:i] + a[i+1:]
    return a

def random_word(letters):
    N = xrange(min(len(letters),max_length),1,-1)
    while 1:
        for n in N:
            for _ in xrange(100):
                s = sort_word(random_subset(letters,n))
                try:
                    return dictionary[s]
                except KeyError:
                    pass

def direction(d):
    dir = zeros(2,dtype=int)
    dir[d] = 1
    return dir

class Node(object):
    __slots__ = ['word','x','d','parent','children']

    def __init__(self,word,x,d,parent):
        self.word = word
        self.x = array(x)
        self.d = d
        self.parent = parent
        self.children = []

    def _map(self,m):
        d = direction(self.d)
        for i in xrange(len(self.word)):
            m[tuple(self.x+i*d)] = self.word[i]
        for c in self.children:
            c._map(m)

    def map(self):
        m = {}
        self._map(m) 
        return m

    def nodes(self):
        yield self
        for c in self.children:
            for n in c.nodes():
                yield n

def print_tree(tree):
    m = tree.map()
    min = zeros(2,dtype=int)
    max = zeros(2,dtype=int)
    for x in m.iterkeys():
        min = minimum(min,x)
        max = maximum(max,x)
    table = zeros(max-min+1,dtype='|S1')
    table[:] = ' '
    for x,c in m.iteritems():
        table[tuple(x-min)] = c.upper()
    for r in xrange(len(table)):
        print ''.join(table[r])

def grow_tree(tree,letters):
    m = tree.map()
    nodes = list(tree.nodes())
    N = xrange(min(len(letters),max_length-1),1,-1)
    for attempt in xrange(100):
        for n in N:
            for _ in xrange(100):
                # Pick a random node
                i = random.randint(len(nodes))
                node = nodes[i]
                # Pick a random starting location
                j = random.randint(len(node.word))
                s,t = direction(node.d),direction(1-node.d)
                x = node.x+j*s
                if tuple(x+t) in m or tuple(x-t) in m:
                    continue
                if 0:
                    print 'start: %s, %s'%(node.word,node.word[j])
                # Pick a random set of letters and see if they make a word
                subset = random_subset(letters,n)
                try:
                    word = dictionary[sort_word(node.word[j]+subset)]
                    if 0:
                        print word
                except KeyError:
                    continue
                # Choose where to attach the word
                places = [k for k in xrange(len(word)) if word[k]==node.word[j]]
                k = places[random.randint(len(places))]
                # Check if the attachment point fits
                fail = 0
                for l in xrange(1,k+1):
                    xp = x-l*t
                    if tuple(xp-t) in m or tuple(xp-s) in m or tuple(xp+s) in m:
                        fail = 1 
                        break
                for l in xrange(1,len(word)-k):
                    xp = x+l*t
                    if tuple(xp+t) in m or tuple(xp-s) in m or tuple(xp+s) in m:
                        fail = 1
                        break
                if fail:
                    break
                # Add word to the tree
                print 'add',word
                child = Node(word,x-k*t,1-node.d,k)
                node.children.append(child)
                return tree,subtract(letters,subset)
    return None

def prune_tree(tree,letters):
    nodes = list(tree.nodes())
    while 1:
        i = random.randint(len(nodes))
        node = nodes[i]
        if node.children:
            continue
        print 'pruning',node.word
        letters = letters + node.word
        if node.parent>=0:
            parent, = [n for n in nodes if node in n.children]
            parent.children.remove(node)
            letters = subtract(letters,node.word[node.parent])
        else:
            tree = None
        return tree,letters

def build_tree(tree,letters,verbose=0):
    while letters:
        print 'letters =',sort_word(letters)
        if tree is None:
            w = random_word(letters)
            print 'start:',w
            letters = subtract(letters,w)
            tree = Node(w,(0,0),1,-1)
        else:
            grow = grow_tree(tree,letters)
            if grow:
                tree,letters = grow
            else:
                tree,letters = prune_tree(tree,letters)
        if verbose:
            print
            print_tree(tree)
            print
    return tree,letters

def play():
    letter_pattern = re.compile('^[a-z]+$')
    while 1:
        letters = raw_input('starting letters: ').lower()
        if not re.match('^[a-z]{21}$',letters):
            print 'bad initial letters'
        else:
            break
    tree = None
    while 1:
        tree,letters = build_tree(tree,letters)
        print
        print_tree(tree)
        print
        while 1:
            peel = raw_input('next letter: ').lower()
            if not re.match('^[a-z]$',peel):
                print 'bad next letter'
            else:
                letters += peel
                break

if __name__=='__main__':
    if 0:
        letters = 'retain'
        letters = 'iremkjuwlohdtdlttgrae'
        random.seed(1371)
        if 0:
            print random_word(letters)
        else:
            build_tree(None,letters)
    else:
        play()
