import argparse
import subprocess

if __name__ == '__main__':
    def create_cypher_node(id, name):
        return "({id} {{name: '{name}'}})".format(id=str(chr(id + 65)), name=name)


    def convert_to_cypher_query(input):
        lines = input.split("\n")

        i = 0
        nodes = []
        nodeIds = []
        rels = []
        for line in lines:
            split_start = line.split('--')  # Split into [start, rel-->end]
            if split_start != ['']:  # As long as valid relationship exists then
                split_end = split_start[1].split("->")  # Split into [rel, end]

                start_obj = split_start[0].replace('(', '').replace(')', '').split(',')
                startId = start_obj[0]
                start = start_obj[1].replace(' ', '')

                start_node = create_cypher_node(int(startId), start)
                exists = False
                for node in nodeIds:
                    if node[0] == startId:
                        start_node = node[1]
                        exists = True
                        break

                if not exists:
                    nodes.append(start_node)
                    nodeIds.append([startId, start_node])
                i += 1

                end_obj = split_end[1].replace('(', '').replace(')', '').split(',')
                endId = end_obj[0]
                end = end_obj[1].replace(' ', '')

                end_node = create_cypher_node(int(endId), end)
                exists = False
                for node in nodeIds:
                    if node[0] == endId:
                        end_node = node[1]
                        exists = True
                        break

                if not exists:
                    nodes.append(end_node)
                    nodeIds.append([endId, end_node])
                i += 1

                rel = split_end[0].replace('[', '').replace(']', '')  # Remove brackets from rel object
                rel_query = "CREATE ({start})-[:{rel}]->({end})".format(start=start_node[1], rel=rel, end=end_node[1])
                rels.append(rel_query)
                i += 1

        query = "CREATE q="
        for node in nodes:
            if not node == nodes[len(nodes) - 1]:
                query = query + node + ","
            else:
                query = query + node + "\n"

        for rel in rels:
            query = query + rel + "\n"

        query = query + "RETURN *"

        return query


    parser = argparse.ArgumentParser()
    parser.add_argument('--sentence', dest='sentence', type=str, help='Input sentence')
    args = parser.parse_args()

    command = 'curl -X POST -F "p=' + args.sentence + '" localhost:9998/stanfordnlp'
    output = subprocess.check_output(command, shell=True, text=True)
    print(convert_to_cypher_query(output.split("§")[0]))
