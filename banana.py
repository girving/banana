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

# Build dictionary
max_length = 7
dictionary = {}
for w in read_words(max_length):
    sw = sort_word(w)
    dictionary[sw] = dictionary.get(sw,()) + (w,)
print 'sorted word count =',len(dictionary)
print 'word count =',sum(len(w) for w in dictionary.itervalues())
for sw,w in tuple(dictionary.items()):
    for j in xrange(len(sw)):
        swp = sw[j] + sw[:j] + sw[j+1:]
        dictionary[swp] = w
print 'expanded dictionary size =',len(dictionary)

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
                    words = dictionary[s]
                    return words[random.randint(len(words))]
                except KeyError:
                    pass

directions = (array([1,0]),array([0,1]))

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
        d = directions[self.d]
        for i in xrange(len(self.word)):
            m[tuple(self.x+i*d)] = self.word[i]
        for c in self.children:
            c._map(m)

    def map(self):
        m = {}
        self._map(m) 
        return m

    def mask(self):
        min = zeros(2,dtype=int)
        max = zeros(2,dtype=int)
        nodes = tuple(self.nodes())
        for n in nodes:
            min = minimum(min,n.x)
            max = maximum(max,n.x+(len(n.word)-1)*directions[n.d])
        min -= max_length+1
        max += max_length+1
        mask = zeros(max-min+1,dtype=bool)
        for n in nodes:
            d = directions[n.d]
            for j in xrange(len(n.word)):
                mask[tuple(n.x+j*d-min)] = True
        return min,mask

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

def measure_space(m,x,s,t):
    space = 0
    while space<max_length:
        x = x+t
        if tuple(x+t) in m or tuple(x-s) in m or tuple(x+s) in m:
            break
        space += 1
    return space

def grow_tree(tree,letters):
    # Build list of start points
    m = tree.map()
    nodes = tuple(tree.nodes())
    starts = []
    for i,node in enumerate(nodes):
        s,t = directions[node.d],directions[1-node.d]
        for j in xrange(len(node.word)):
            c = node.word[j]
            x = node.x+j*s
            if tuple(x+t) not in m and tuple(x-t) not in m:
                before = measure_space(m,x,s,-t)
                after  = measure_space(m,x,s, t)
                if before or after:
                    starts.append((c,before,after,(i,x)))
    # Try all possible subsets everywhere
    for n in xrange(min(len(letters),max_length-1),0,-1):
        for subset in subsets(letters,n):
            subset = sort_word(subset)
            for c,before,after,ix in starts:
                for word in dictionary.get(c+subset,()):
                    for k in xrange(len(word)):
                        if word[k]==c and before>=k and after>=len(word)-1-k:
                            i,x = ix
                            new_tree = copy.deepcopy(tree)
                            node = list(new_tree.nodes())[i]
                            d = 1-node.d
                            node.children.append(Node(word,x-k*directions[d],d,k))
                            yield new_tree,subtract(letters,subset),word

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
                next.append((tt,ll,words+(word,)))
        for t,l,w in next:
            s = t.signature()
            if s not in done:
                done.add(s)
                print 'maybe pruning %s (letters = %s)'%(', '.join(w),l)
                yield copy.deepcopy(t),l,w

def finish_tree(tree,letters,bad):
    tree = copy.deepcopy(tree)
    if not letters:
        yield tree,[]
    else:
        for tree,letters,word in grow_tree(tree,letters):
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
            tree,letters,word = grow_tree(tree,letters).next()
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
    try:
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
    except EOFError:
        pass

def autoplay():
    letters = 'iremkjuwlohdtdlttgrae'
    tree = None
    s = None
    for c in 'abcdefg ':
        tree = build_tree(tree,letters)
        letters = ''
        s = hash((s,tree.signature()))
        print 'hash =',s
        if c==' ':
            break
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
    elif 1:
        random.seed(1731)
        autoplay()
    else:
        play()
