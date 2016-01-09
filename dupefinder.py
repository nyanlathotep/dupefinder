import re

def listJoin(items):
  if (len(items) == 0):
    return ''
  elif (len(items) == 1):
    return items[0]
  elif (len(items) == 2):
    return ' and '.join(items)
  else:
    return ', '.join(items[:-1] + ['and ' + items[-1]])



class Thing(object):
  def __init__(self, name, id):
    object.__init__(self)
    self.name = name
    self.id = id
    self.counts = {}
    
  def count(self, group):
    self.counts[group.id] = self.counts.get(group.id, 0) + 1

class Group(object):
  def __init__(self, name, id):
    object.__init__(self)
    self.name = name
    self.id = id
    self.counts = {}
    
  def count(self, thing):
    self.counts[thing.id] = self.counts.get(thing.id, 0) + 1

class GroupGroup(object):
  def __init__(self, names= None, contents= None):
    object.__init__(self)
    self.things = {}
    self.groups = {}
    self.filter = None
    self.filtermode = None

    self.ruleHandlers = {
      'common': self.getCommons,
      'dupe': self.getDupes,
      'unique': self.getUniques
    }

    self.renderHandlers = {
      'short': self.shortReport,
      'verbose': self.verboseReport
    }

    self.verboseRenderers = {
      'common': self.verboseCommon,
      'dupe': self.verboseDupe,
      'unique': self.verboseUnique
    }

    self.update(names, contents)

  def update(self, names= None, contents= None):
    if (names):
      self.addGroups(names)
    if (names and contents):
      self.addThings(contents)

  def addGroups(self, names):
    for name in names:
      self.addGroup(name)

  def addThings(self, contents):
    for i in range(len(contents)):
      for thing in contents[i]:
        self.addThing(thing, self.groups[i])

  def thingName(self, thingid, tag= None):
    name = self.things[thingid].name
    if (tag == None):
      return name
    else:
      return str(tag) + name + str(-tag)

  def groupName(self, groupid):
    return self.groups[groupid].name
    
  def addGroup(self, name):
    groupid = len(self.groups)
    self.groups[groupid] = Group(name, groupid)
    return self.groups[groupid]
    
  def addThing(self, name, group):
    thingid = name.lower()
    if (thingid not in self.things):
      self.things[thingid] = Thing(name, thingid)
    thing = self.things[thingid]
    group.count(thing)
    thing.count(group)
    return thing

  def setFilter(self, group= None, mode= None):
    if (not group):
      self.filter = None
      self.filtermode = None
      return
    self.filtermode = mode
    self.filter = []
    for name in group:
      thingid = name.lower()
      if (thingid in self.things):
        self.filter.append(thingid)

  def checkFilter(self, thingid):
    if (not self.filter): return False
    return (thingid in self.filter) == self.filtermode

  def filterThings(self):
    for thing in self.things:
      if (self.checkFilter(thing)): continue
      yield thing

  def getCommons(self, arg):
    commons = {}
    for thing in self.filterThings():
      tcounts = self.things[thing].counts
      if (len(tcounts) in arg):
        commons[thing] = tcounts.keys()
    return commons

  def getDupes(self, arg):
    dupes = {}
    for thing in self.filterThings():
      tcounts = self.things[thing].counts
      counts = {x:tcounts[x] for x in tcounts if tcounts[x] in arg}
      if (counts):
        dupes[thing] = counts
    return dupes

  def getUniques(self, arg):
    uniques = {}
    for thing in self.filterThings():
      tcounts = self.things[thing].counts
      if (len(tcounts) == 1 and list(tcounts.values())[0] == 1):
        uniques[thing] = list(tcounts.keys())[0] 
    return uniques

  def buildReport(self, **args):
    data = {}
    for arg in args:
      if (args[arg] is not False and arg in self.ruleHandlers):
        data[arg] = self.ruleHandlers[arg](args[arg])
    report = {}
    for thingid in self.things:
      thingdata = {}
      for rule in data:
        if (thingid in data[rule]):
          thingdata[rule] = data[rule][thingid]
      if (args['all'] and len(thingdata) < len(data)):
        continue
      if (len(thingdata) > 0):
        report[thingid] = thingdata
    return report

  def renderReport(self, report, format, **args):
    return self.renderHandlers[format](report, **args)

  def shortReport(self, report, **args):
    if (len(report) > 0):
      report = [self.thingName(x, args['tag']) for x in report]
      report.sort()
      return '\n'.join(report)
    else:
      return ''

  def verboseCommon(self, commons, **args):
    return 'common to %s' % listJoin([self.groupName(x) for x in commons])

  def verboseDupe(self, dupes, **args):
    items = ['%s (%d)' % (self.groupName(x), dupes[x]) for x in dupes]
    return 'duplicated in %s' % listJoin(items)

  def verboseUnique(self, unique, **args):
    return 'unique to %s' % self.groupName(unique)

  def verboseReport(self, report, **args):
    items = []
    rules = sorted(list(self.verboseRenderers.keys()))
    things = sorted(list(report.keys()), key= lambda x: self.thingName(x))
    for item in things:
      entry = []
      for rule in rules:
        if rule in report[item]:
          entry.append(self.verboseRenderers[rule](report[item][rule], **args))
      entry = self.thingName(item, args['tag']) + ': ' + '; '.join(entry)
      items.append(entry)
    return '\n'.join(items)



def oneItemPerLineCodec(data):
  # strip lines and remove comments
  data = [x.strip() for x in data.split('\n')]
  data = [x for x in data if (x == '' or x[0] != '#')]

  # break up groups by blank lines
  groups = []
  while ('' in data):
    i = data.index('')
    if (i != 0):
      groups.append(data[:i])
    data = data[data.index('') + 1:]
  if (data):
    groups.append(data)

  # determine named groups
  names = []
  for group in groups:
    if (len(group) > 1 and re.match(r'-+$', group[1])):
      names.append(group[0])
      del group[:2]
    else:
      names.append(None)

  # autoname unnamed groups
  c = 1
  for i in range(len(names)):
    if (names[i] is None):
      while (('Group %d' % c) in names): c += 1
      names[i] = 'Group %d' % c
      c += 1

  return names, groups



class Tag(object):
  tagRe = [
    (re.compile(r'\[(\w+)\]'), 'bb', True),
    (re.compile(r'\[/(\w+)\]'), 'bb', False),
    (re.compile(r'<(\w+)>'), 'html', True),
    (re.compile(r'</(\w+)>'), 'html', False)
  ]
  renderers = {
    'bb': lambda b, o: '[' +  ('' if o else '/') + b + ']',
    'html': lambda b, o: '<' +  ('' if o else '/') + b + '>'
  }
  def __init__(self, string= None, body= None, kind= None, start= None):
    object.__init__(self)
    if string:
      found = False
      for rule in self.tagRe:
        match = rule[0].match(string)
        if (match):
          self.body = match.group(1)
          self.kind, self.start = rule[1:]
          found = True
          break
      if (not found):
        raise ValueError('unknown tag format')
    else:
      self.body = body
      self.kind = kind
      self.start = start

  def __str__(self):
    return self.renderers[self.kind](self.body, self.start)

  def __neg__(self):
    return Tag(None, self.body, self.kind, not self.start)



class IntRange(object):
  def __init__(self, start, stop):
    object.__init__(self)
    if (start is None and stop is None):
      raise ValueError('IntRange cannot be unbounded on both sides')
    if (start is not None and stop is not None and start > stop):
      start, stop = stop, start
    self.start = start
    self.stop = stop

  def __contains__(self, item):
    if (self.start is not None and item < self.start):
      return False
    if (self.stop is not None and item > self.stop):
      return False
    return True

  def __or__(self, other):
    if (other.start in self and other.stop in self):
      return IntRange(self.start, self.stop)
    elif (self.start in other and self.stop in other):
      return IntRange(other.start, other.stop)
    elif (self.start in other):
      return IntRange(other.start, self.stop)
    elif (self.stop in other):
      return IntRange(self.start, other.stop)
    else:
      raise ValueError('ranges do not overlap')

  def __repr__(self):
    return 'IntRange(%d,%d)' % (self.start, self.stop)

class MultiRange(object):
  rangeRe = re.compile(r'(\d*):(\d*)')
  def __init__(self, string= None):
    object.__init__(self)
    self.ranges = []
    if (string):
      for item in string.split(','):
        match = self.rangeRe.match(item)
        if (match):
          start, stop = [None if x is '' else int(x) for x in match.groups()]
          self.addRange(start, stop)
        else:
          item = int(item)
          self.addRange(item, item)

  def addRange(self, start, stop):
    r = IntRange(start, stop)
    rs = self.ranges
    self.ranges = []
    while (len(rs)):
      r2 = rs.pop()
      if (r.start in r2 or r.stop in r2):
        r = r | r2
      else:
        self.ranges.append(r2)
    self.ranges.append(r)

  def __contains__(self, item):
    for r in self.ranges:
      if (item in r):
        return True
    return False

  def __repr__(self):
    rs = []
    self.ranges.sort(key= lambda x: x.start)
    for r in self.ranges:
      if (r.start == r.stop):
        rs.append('%d' % r.start)
      else:
        rs.append('%d:%d' % tuple('' if x is None else x for x in (r.start, r.stop)))
    return ','.join(rs)



if (__name__ == '__main__'):
  import sys, argparse

  parser = argparse.ArgumentParser()
  
  analysisgroup = parser.add_argument_group('Analysis Rules')
  analysisgroup.add_argument('-c', '--common', help= 'shows items that some number of lists have in common; syntax is comma separated ranges or items, e.g. 2:5  4,6  2:  :3,5  (default: 2:)', nargs= '?', const= '2', default= False, type= MultiRange, metavar= 'vals')
  analysisgroup.add_argument('-d', '--dupe', help= 'shows items that are duplicated in at least one list some number of times; syntax is the same as -c (default: 2:)', nargs= '?', const= '2:', default= False, type= MultiRange, metavar= 'vals')
  analysisgroup.add_argument('-u', '--unique', action= 'store_true', help= 'shows items that only appear once and in only one list')
  analysisgroup.add_argument('-a', '--all', action= 'store_true', help= 'items must meet all other selected rules to appear in reports')

  filteringgroup = parser.add_mutually_exclusive_group()
  filteringgroup.add_argument('-f', '--blacklist', help= 'sets a given group to function as a blacklist; any things present in the group will not appear in the report', metavar= 'group')
  filteringgroup.add_argument('-F', '--whitelist', help= 'sets a given group to function as a whitelist; only things present in the group will appear in the report', metavar= 'group')

  # report format options
  reportgroup = parser.add_mutually_exclusive_group()
  reportgroup.add_argument('-v', '--verbose', action= 'store_const', help= 'generates a verbose report', dest= 'format', const= 'verbose')
  parser.set_defaults(format= 'short')

  # other options
  parser.add_argument('-L', '--list-groups', action= 'store_true', help= 'list all groups present in input files')
  parser.add_argument('-l', '--list-things', action= 'store_true', help= 'list all things present in input files')
  parser.add_argument('-o', '--out', help= 'file to output to instead of printing')
  parser.add_argument('-t', '--tag', help= 'adds BBCode or HTML tags to wrap names of list items (default: [c]); note that the windows shell is wonky and to use an HTML tag, you need to do it like so: ^<tagname^>', nargs= '?', const= '[c]', default= None, type= Tag)
  parser.add_argument('infiles', help= 'file(s) to read from', metavar= 'filepath', nargs='+')
  
  args = parser.parse_args()

  ruleArgs = ['common', 'dupe', 'unique', 'all']
  ruleArgs = {x:vars(args)[x] for x in ruleArgs}

  reportArgs = ['tag']
  reportArgs = {x:vars(args)[x] for x in reportArgs}

  names, groups = [], []
  for path in args.infiles:
    fp = open(path)
    n, g = oneItemPerLineCodec(fp.read())
    fp.close()
    names += n
    groups += g

  filtergroup, filtermode = None, None
  if (args.whitelist or args.blacklist):
    groupname = args.whitelist if args.whitelist else args.blacklist
    groupre = re.compile(re.escape(groupname))
    inds = []
    for i in range(len(names)):
      if (groupre.match(names[i])):
        inds.append(i)
    if (len(inds) > 1):
      sys.stderr.write('error: could not apply whitelist/blacklist\n')
      error = 'ambiguous substring "%s": multiple groups match (%s)\n' % (groupname, listJoin([names[i] for i in inds]))
      sys.stderr.write(error)
      exit(0)
    elif (len(inds) == 0):
      sys.stderr.write('error: could not apply whitelist/blacklist')
      sys.stderr.write('substring "%s" does not match any group in input files' % groupName)
      exit(0)
    filtergroup = groups[inds[0]]
    filtermode = args.blacklist is not None
    names = names[:inds[0]] + names[inds[0]+1:]
    groups = groups[:inds[0]] + groups[inds[0]+1:]

  gg = GroupGroup(names, groups)
  if (args.whitelist or args.blacklist):
    gg.setFilter(filtergroup, filtermode)
      
  outstream = open(args.out, 'w') if args.out else sys.stdout

  if (args.list_groups):
    outstream.write('Input files contain %d groups:\n' % len(gg.groups))
    for groupid in gg.groups:
      outstream.write('* %s\n' % gg.groups[groupid].name)
    outstream.write('---------------------\n\n')

  if (args.list_things):
    outstream.write('Input files contain %d things:\n' % len(gg.things))
    for thingid in gg.things:
      outstream.write('* %s\n' % gg.things[thingid].name)
    outstream.write('---------------------\n\n')

  doRender = len([x for x in ruleArgs.values() if x is not False]) >= 1
  if (doRender):
    report = gg.buildReport(**ruleArgs)
    if (report):
      outstream.write(gg.renderReport(report, args.format, **reportArgs))

    if (args.out):
      outstream.close()
