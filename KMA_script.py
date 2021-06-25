import csv
import itertools

# ReadInQueryTerms imports local CSV of Google Scholar query terms
def ReadInQueryTerms():
    # read csv file as a list of lists
    with open('QueryTerms.csv', 'r', encoding='utf-8-sig') as read_obj:
        # pass the file object to reader() to get the reader object
        csv_reader = csv.reader(read_obj)
        # Pass reader object to list() to get a list of lists
        return list(csv_reader)

# BuildQueryMaps Takes CSV Import Data and transforms it into two dictionaries
# (Maps). Qidx, which is used to identify the key of a discpline using an
# index number, and QMap, which is used to call either the include or disclude
# query terms
def BuildQueryMaps(QueryTerms):
    Qidx = {} 
    Qmap = {}
    for idx in range(len(QueryTerms)):
        Qidx[idx] = QueryTerms[idx][0]
        Qmap[QueryTerms[idx][0]] = [QueryTerms[idx][2],QueryTerms[idx][1]]
    return Qidx, Qmap

# getAllCombinations generates all possible include/disclude combinations, and
# returns them as a list of tuples. It excludes a single all-Disclude
# combination
def getAllCombinations(n):
    LIST = list(itertools.product([False,True],repeat=n))
    return LIST[1:len(LIST)]


# QueryMap retrieves requested include/disclude query terms.
class QueryMap:
    def __init__(self):
        self.Qidx, self.Qmap = BuildQueryMaps(ReadInQueryTerms())
    def getQueryTerm(self,Qidx,Include):
        if Include:
            return self.Qmap[self.Qidx[Qidx]][1]
        return self.Qmap[self.Qidx[Qidx]][0]

# GetQueryTerms uses a QueryMap to pull all necessary include/disclude terms
# to build a statement based on a combination-tuple of true/false designations
def GetQueryTerms(Combination, Qmap):
    qterms = []
    for idx in range(len(Combination)):
        qterms.append(Qmap.getQueryTerm(idx,Combination[idx]))
    return qterms
        
# BuildQueryStatement uses a list of query terms to build a parsable search
# string
def BuildQueryStatement(TermsList):
    queryStatement = ""
    for i in TermsList:
        queryStatement += i +" "
    return queryStatement[0:len(queryStatement)-2]

# ProduceAllQueryStatements produces all query statements
def ProduceAllQueryStatements():
    Qmap = QueryMap()
    Combinations = getAllCombinations(len(Qmap.Qmap.keys()))
    QStatements = []
    for Combination in Combinations:
        QStatements.append(BuildQueryStatement(GetQueryTerms(Combination, Qmap)))
    return QStatements, Combinations

def WriteQueryStatementsToFile2(Results):
    with open('QueryStatements.csv','w') as result_file:
        csv_writer = csv.writer(result_file, dialect='excel')
        csv_writer.writerows(Results)
        
def WriteQueryStatementsToFile(Results):
    with open('QueryStatements.csv','w') as result_file:
        for Result in Results:
            result_file.write('%s\n' % Result)

# WriteCombinationsToFile writes all combinations to file
def WriteCombinationsToFile(Combinations):
    with open('Combinations.csv','w') as result_file:
        for Combination in Combinations:
            formatString = ""
            for item in Combination:
                if item:
                    formatString+="TRUE,"
                else:
                    formatString+="FALSE,"
            result_file.write('%s\n' % formatString)
    
def RunStage1():
    Qstatements,Combinations = ProduceAllQueryStatements()
    WriteQueryStatementsToFile(Qstatements)
    WriteCombinationsToFile(Combinations)

#%%

class ResultContainer:
    def __init__(self,row):
        self.value = int(row[7])
        self.combination = {}
        self.isolated = False # isolated indicates only 1 term used
        count = 0
        for idx in range(7):
            if row[idx] =="TRUE":
                count += 1
                self.combination[idx] = True
            else:
                self.combination[idx] = False
        if count == 1:
            self.isolated = True
    def includes(self,idx):
        return self.combination[idx]
    def getValue(self):
        return self.value

# GetAllDyadPairs gets a list of combinations of edges between different
# indexes
def GetAllDyadPairs():
    a = 7
    b = 0
    c = []
    while a > 0:
        for i in range(b+1,7):
            c.append([b,i])
        a -= 1
        b += 1
    return c

# ReadInResults takes prior results and builds them into objects for use by
# other functions
def ReadInResults():
    f = "Results_File_a.csv"
    # read csv file as a list of lists
    with open(f, 'r', encoding='utf-8-sig') as read_obj:
        # pass the file object to reader() to get the reader object
        csv_reader = csv.reader(read_obj)
        # Pass reader object to list() to get a list of lists
        Rows = list(csv_reader)
    results = []
    for row in Rows:
        results.append(ResultContainer(row))
    return results
        
# EdgeBuilder manages the state of edges
class EdgeBuilder:
    def __init__(self,NodeA,NodeB):
        self.NodeA = NodeA
        self.NodeB = NodeB
        self.ct = 0
    def addToCount(self,value):
        self.ct += value
    def writeToCsvString(self, Id):
        string = ""
        string += str(self.NodeA)+", "
        string += str(self.NodeB)+", "
        string += "Undirected, "
        string += str(Id) + ", "
        string += str(self.ct)
        return string
    
# CreateEdges creates a list of Edge Strings for Gephi Import
def CreateEdges(Results):
    edges = []
    # Get all dyad pair edges
    dyadpairs = GetAllDyadPairs()
    for pair in dyadpairs:
        edge = EdgeBuilder(pair[0],pair[1])
        for result in Results:
            if result.includes(edge.NodeA) and result.includes(edge.NodeB):
                edge.addToCount(result.getValue())
        edges.append(edge)
    
    # Get all self-edges, cases where no other term was cited
    for idx in range(7):
        edge = EdgeBuilder(idx,idx)
        for result in Results:
            if result.isolated:
                if result.includes(idx):
                    edge.addToCount(result.getValue())
        edges.append(edge)
               
    # Build edgeStrings
    edgeStrings = []
    edgeStrings.append("Source,Target,Type,Id,Weight")
    for idx in range(len(edges)):
        if edges[idx].ct > 0: 
            edgeStrings.append(edges[idx].writeToCsvString(idx))
    return edgeStrings
                    
# writeEdgesToFile writes edge strings to file
def writeEdgesToFile(edges):
    with open('edges.csv','w') as result_file:
        for edge in edges:
            result_file.write('%s\n' % edge)
        
# writeNodesToFile writes node strings to file
def writeNodesToFile(nodes):
    with open('nodes.csv','w') as result_file:
        for node in nodes:
            result_file.write('%s\n' % node)
            
def CreateNodes():
    Qmap = QueryMap()
    nodeStrings = []
    nodeStrings.append("Id,Label")
    for idx in range(7):
        nodeStrings.append(str(idx) + ", "+ Qmap.Qidx[idx])
    return nodeStrings
    
def RunStage2():
    Results = ReadInResults()
    edgeStrings = CreateEdges(Results)
    writeEdgesToFile(edgeStrings)
    nodeStrings = CreateNodes()
    writeNodesToFile(nodeStrings)
    

#%%


        
        




        
        
        