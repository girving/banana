#!/usr/bin/env python

import os
import re
from numpy import *
import copy

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

def subsets(s,n):
    """Return all substrings of size n."""
    if not n:
        yield ''
    else:
        n -= 1
        for i in xrange(len(s)-n):
            c = s[i]
            for sp in subsets(s[i+1:],n):
                yield c+sp

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

    def __deepcopy__(self,m):
        n = Node(self.word,self.x,self.d,self.parent)
        for c in self.children:
            n.children.append(copy.deepcopy(c,m))
        return n

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

    def signature(self):
        return (self.word,tuple(self.x),self.d,self.parent,tuple(c.signature() for c in self.children))

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
        print '   ',' '.join(table[r])
    # Blah
    if 0:
        nodes = tree.nodes()
        for n in nodes:
            if n.word=='grout':
                print 'grout has %d children: %s'%(len(n.children),' '.join(c.word for c in n.children))
            for c in n.children:
                if c.word=='gled':
                    print 'gled beneath',n.word

def check_start(m,x,t):
    return not (tuple(x+t) in m or tuple(x-t) in m)

def check_space(m,x,t,word,k):
    s = (1,1)-t
    for l in xrange(1,k+1):
        xp = x-l*t
        if tuple(xp-t) in m or tuple(xp-s) in m or tuple(xp+s) in m:
            return False
    for l in xrange(1,len(word)-k):
        xp = x+l*t
        if tuple(xp+t) in m or tuple(xp-s) in m or tuple(xp+s) in m:
            return False
    return True

def grow_tree(tree,letters,attempts=20000):
    m = tree.map()
    nodes = list(tree.nodes())
    N = xrange(min(len(letters),max_length-1),0,-1)
    while attempts>=0:
        for n in N:
            for _ in xrange(100):
                attempts -= 1
                # Pick a random node
                i = random.randint(len(nodes))
                node = nodes[i]
                # Pick a random starting location
                j = random.randint(len(node.word))
                s,t = direction(node.d),direction(1-node.d)
                x = node.x+j*s
                if not check_start(m,x,t):
                    continue
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
                if not check_space(m,x,t,word,k):
                    continue
                # Add word to the tree
                print 'add',word
                child = Node(word,x-k*t,1-node.d,k)
                node.children.append(child)
                return tree,subtract(letters,subset)
    return None

def grow_tree_exhaustive(tree,letters):
    m = tree.map()
    nodes = list(tree.nodes())
    for n in xrange(min(len(letters),max_length-1),0,-1):
        for subset in subsets(letters,n):
            for i,node in enumerate(nodes):
                s,t = direction(node.d),direction(1-node.d)
                for j in xrange(len(node.word)):
                    x = node.x+j*s
                    if check_start(m,x,t):
                        try:
                            word = dictionary[sort_word(node.word[j]+subset)]
                        except KeyError:
                            continue
                        for k in xrange(len(word)):
                            if word[k]==node.word[j] and check_space(m,x,t,word,k):
                                child = Node(word,x-k*t,1-node.d,k)
                                if 0 and word=='rec':
                                    print '---------------------'
                                    print 'adding rec'
                                    print 'child count:',len(node.children)
                                new_tree = copy.deepcopy(tree)
                                new_node = list(new_tree.nodes())[i]
                                new_node.children.append(child)
                                if 0 and word=='rec':
                                    print 'child count:',len(new_node.children)
                                    print_tree(tree)
                                    print '---'
                                    print_tree(new_tree)
                                    print '---------------------'
                                yield new_tree,subtract(letters,subset),word

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

def singly_pruned_trees(tree,letters):
    nodes = list(enumerate(tree.nodes()))
    nodes.sort(key=lambda n:len(n[1].word))
    for i,node in nodes:
        if not node.children:
            new_letters = letters + node.word 
            if node.parent>=0:
                new_tree = copy.deepcopy(tree) 
                new_nodes = list(new_tree.nodes())
                node = new_nodes[i]
                parent, = [n for n in new_nodes if node in n.children]
                parent.children.remove(node)
                new_letters = subtract(new_letters,node.word[node.parent])
                yield new_tree,new_letters,node.word

def pruned_trees(tree,letters):
    done = set()
    done.add(tree.signature())
    next = [(tree,letters,())]
    while 1:
        old,next = next,[]
        for t,l,words in old:
            for tt,ll,word in singly_pruned_trees(t,l):
                if word=='gled':
                    print '----------------------'
                    print 'prune',words,word
                    print_tree(t)
                    print '----'
                    print_tree(tt)
                    print '----------------------'
                next.append((tt,ll,words+(word,)))
        for t,l,w in next:
            s = t.signature()
            if s not in done:
                done.add(s)
                #print_tree(t)
                if 1 or l not in 'tgrd tgrl tgrtth tgrdl tgrdtth tgrltth tgrdltth'.split():
                    print 'maybe pruning %s (letters = %s)'%(', '.join(w),l)
                    yield copy.deepcopy(t),l,w

def finish_tree(tree,letters,bad):
    tree = copy.deepcopy(tree)
    if not letters:
        yield tree,[]
    else:
        for tree,letters,word in grow_tree_exhaustive(tree,letters):
            s = tree.signature(),sort_word(letters)
            if s not in bad:
                success = False
                for tree,words in finish_tree(tree,letters,bad):
                    success = True
                    yield tree,[word]+words
                if not success:
                    bad.add(s)

def greedily_expand_tree(tree,letters):
    words = []
    if tree is None:
        w = random_word(letters)
        words.append(w)
        letters = subtract(letters,w)
        tree = Node(w,(0,0),1,-1)
    while letters:
        try:
            tree,letters,word = grow_tree_exhaustive(tree,letters).next()
            words.append(word)
        except StopIteration:
            break
    return tree,letters,words

def fix_tree(tree,letters):
    bad = set([(tree.signature(),sort_word(letters))])
    for tree,letters,pruned in pruned_trees(tree,letters):
        for tree,added in finish_tree(tree,letters,bad):
            print 'pruned %s'%', '.join(pruned)
            print 'added %s'%', '.join(added)
            return tree
    raise RuntimeError('failed')

def build_tree(tree,letters,verbose=0):
    tree,letters,words = greedily_expand_tree(tree,letters)
    if words:
        print 'add %s'%(', '.join(words))
        print_tree(tree)
    if letters:
        print 'letters =',letters
        tree = fix_tree(tree,letters)
        print_tree(tree)
    return tree

def play():
    letter_pattern = re.compile('^[a-z]+$')
    while 1:
        letters = raw_input('starting letters: ').lower()
        if not re.match('^[a-z]{21,}$',letters):
            print 'bad initial letters'
        else:
            break
    tree = None
    while 1:
        tree = build_tree(tree,letters)
        letters = ''
        print '--------------------------'
        while 1:
            peel = raw_input('next letter: ').lower()
            if not re.match('^[a-z]$',peel):
                print 'bad next letter'
            else:
                letters += peel
                break

def autoplay():
    letters = 'iremkjuwlohdtdlttgrae'
    tree = None
    for c in 'abcdefg':
        tree = build_tree(tree,letters)
        letters = ''
        print '--------------------------'
        print
        print 'peel:',c
        letters += c

if __name__=='__main__':
    if 0:
        letters = 'retain'
        letters = 'iremkjuwlohdtdlttgrae'
        random.seed(1371)
        if 0:
            print random_word(letters)
        else:
            build_tree(None,letters)
    elif 0:
        random.seed(1731)
        autoplay()
    else:
        play()
