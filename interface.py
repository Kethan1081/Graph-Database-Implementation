from neo4j import GraphDatabase

class Interface:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self._driver.verify_connectivity()

    def close(self):
        self._driver.close()

    def graphCheck(self):
        with self._driver.session() as session:
            result = session.run("CALL gds.graph.exists('kethan') YIELD exists")
            present = result.single()["exists"]
            print(present)
            if not present:
                session.run('''CALL gds.graph.project('kethan',{Location:{properties :'name'}}, {TRIP:{properties:["distance", "fare"]}})''')

            else:
                session.run('''CALL gds.graph.drop('kethan', true)''')
                session.run('''CALL gds.graph.project('kethan',{Location:{properties :'name'}},{TRIP:{properties:["distance", "fare"]}})''')

    def bfs(self, start_node, last_node):
        # TODO: Implement this method
        self.graphCheck()
        bfs = """
        MATCH (source:Location{name:$s})
        MATCH (target:Location{name:$e})
        CALL gds.bfs.stream('kethan', {sourceNode: id(source), targetNodes: id(target)})
        YIELD path
        RETURN nodes(path) AS path
        """
        res = []
        with self._driver.session() as session:
            # session.run('''CALL gds.graph.drop('myGraph', true)''')
            result = session.run(bfs, s=start_node, e=last_node)
            if result.peek():
                vals = result.single()
                if "path" in vals.keys():
                    res.append(vals)
            else:
                pass
        return res

        #raise NotImplementedError

    def pagerank(self, max_iterations, weight_property):
        # TODO: Implement this method
        self.graphCheck()
        pr = """
        CALL gds.pageRank.stream('kethan',{relationshipWeightProperty: $weight_property, maxIterations: $max_iterations, dampingFactor: 0.85 })
        YIELD nodeId, score WITH gds.util.asNode(nodeId) AS node, score
        ORDER BY score DESC LIMIT 1
        WITH node["name"] AS max_node, score AS max_score
        CALL gds.pageRank.stream('kethan',{relationshipWeightProperty: $weight_property, maxIterations: $max_iterations, dampingFactor: 0.85 })
        YIELD nodeId, score WITH max_node, max_score, gds.util.asNode(nodeId) AS node, score
        ORDER BY score ASC LIMIT 1
        RETURN max_node, max_score, node["name"] AS min_node, score AS min_score
        """
        res = []
        with self._driver.session() as session:
            # session.run('''CALL gds.graph.project('myGraph',
            # {Location:{properties :'name'}},
            # {TRIP:{properties:"distance"}}
            # )''')
            result = session.run(pr, weight_property=weight_property, max_iterations=max_iterations)

            if result.peek():
                vals = result.single()
                max_node = {}
                max_node['name'] = vals["max_node"]
                max_node['score'] = vals["max_score"]
                
                min_node = {}
                min_node['name'] = vals["min_node"]
                min_node['score'] = vals["min_score"]
                res.append(max_node)
                res.append(min_node)
            else:
                pass
        return res
        #raise NotImplementedError