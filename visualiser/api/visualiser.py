from flask import Flask, request, jsonify
from flask_cors import CORS
import yaml

import main

import json
import os.path

from starlette.responses import HTMLResponse, FileResponse

import parsers.NestedTables
from parsers.GSMExt import to_vis_nodes, to_vis_network_phi, to_vis_network_node
from parsers.ReadGSMExt import deserialize_gsm_file

import base64
from io import BytesIO

# origins = [
#     "http://localhost",
#     "http://localhost:9999",
# ]

N_result = dict()
E_result = dict()
N_input = dict()
E_input = dict()
N_removed = dict()
N_inserted = dict()

app = Flask(__name__)
# app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.route('/')
def index():
    return 'hello'


@app.route('/sentences', methods=['POST'], strict_slashes=False)
# @cross_origin()
def update_sentences():
    sentences = request.json['sentences']
    config = request.json['config']

    with open('config.yaml') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)
        for cKey, cValue in config.items():
            cfg[cKey] = cValue
            print(f"Updated {cKey} to {cValue}")

    main.start_pipeline(sentences, cfg)

    return 'Finished pipeline'


@app.route('/log', methods=['GET'])
def get_log():
    with open('config.yaml') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)

        with open(f"{cfg['web_dir']}/log.txt", "r+") as l:
            log = l.readlines()
            # print(log)
            try:
                line = log.pop()
                # print(log)
                l.writelines(log)
            except IndexError as e:
                return 'Waiting...'

    return jsonify({'log': line})


# __author__ = "Giacomo Bergami"
# __copyright__ = "Copyright 2023"
# __credits__ = ["Giacomo Bergami"]
# __license__ = "GPL"
# __version__ = "3.0"
# __maintainer__ = "Giacomo Bergami"
# __email__ = "bergamigiacomo@gmail.com"
# __status__ = "Production"

# import os

def html_base64_image(fig):
    tmpfile = BytesIO()
    fig.savefig(tmpfile, format='png')
    encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
    return '<img src=\'data:image/png;base64,{}\'>'.format(encoded)


@app.route("/morphisms/<dataset>/<folder>", methods=['GET'])
def morphisms(dataset, folder):
    return parsers.NestedTables.generate_morphism_html(os.path.join("/home/fox/PycharmProjects/news-crawler2/visualiser/src/results", dataset, "data", folder), folder)


def load_nodes_any(dataset, folder, N, file):
    new_folder = f"{dataset}/{folder}"
    if new_folder not in N:
        N[new_folder] = dict()
        for obj in deserialize_gsm_file(os.path.join("/home/fox/PycharmProjects/news-crawler2/visualiser/src/results", dataset, "data", folder, file)):
            N[new_folder][obj.id] = obj
    return N


def load_edges_any(dataset, folder, N, E, file):
    new_folder = f"{dataset}/{folder}"
    N = load_nodes_any(dataset, folder, N, file)
    if new_folder not in E:
        E[new_folder] = to_vis_network_phi(N[new_folder].values())
    return (N, E)


def load_result_nodes(dataset, folder):
    global N_result
    N_result = load_nodes_any(dataset, folder, N_result, "result.json")
    # if folder not in N:
    #     N[folder] = dict()
    #     for obj in deserialize_gsm_file(os.path.join(os.getcwd(),"data",folder,"result.json")):
    #         N[folder][obj.id] = obj


def load_input_nodes(dataset, folder):
    new_folder = f"{dataset}/{folder}"
    global N_input
    global N_removed
    global N_inserted
    with open(os.path.join("/home/fox/PycharmProjects/news-crawler2/visualiser/src/results", dataset, "data", folder, "removed.json"), "r") as f:
        N_removed[new_folder] = set(json.load(f))
    with open(os.path.join("/home/fox/PycharmProjects/news-crawler2/visualiser/src/results", dataset, "data", folder, "inserted.json"), "r") as f:
        N_inserted[new_folder] = set(json.load(f))
    N_input = load_nodes_any(dataset, folder, N_input, "input.json")


def load_result_edges(dataset, folder):
    global N_result
    global E_result
    (N_result, E_result) = load_edges_any(dataset, folder, N_result, E_result, "result.json")


def load_input_edges(dataset, folder):
    global N_input
    global E_input
    (N_input, E_input) = load_edges_any(dataset, folder, N_input, E_input, "input.json")


@app.route("/result/nodes/<dataset>/<folder>", methods=['GET'])
def nodes(dataset, folder):
    new_folder = f"{dataset}/{folder}"
    load_input_nodes(dataset, folder)
    load_result_nodes(dataset, folder)
    global N_result
    return to_vis_nodes(N_result[new_folder].values(), None, N_inserted[new_folder])


@app.route("/input/nodes/<dataset>/<folder>", methods=['GET'])
def inodes(dataset, folder):
    new_folder = f"{dataset}/{folder}"
    load_input_nodes(dataset, folder)
    global N_input
    global N_removed
    global N_inserted
    return to_vis_nodes(N_input[new_folder].values(), N_removed[new_folder], N_inserted[new_folder])


@app.route("/result/node/<dataset>/<folder>/<id>", methods=['GET'])
def node(dataset, folder, id):
    new_folder = f"{dataset}/{folder}"
    load_input_nodes(dataset, folder)
    load_result_nodes(dataset, folder)
    global N_result
    global N_inserted
    return to_vis_network_node(N_result[new_folder][int(id)], None, N_inserted[new_folder])


@app.route("/javascript/<file>", methods=['GET'])
def javascript(file):
    with open(file) as f:
        return f.read()


# class CSSResponse(Response):
#     media_type = "text/css"


@app.route("/css/<file>", methods=['GET'])
def javascript_css(file):
    with open(file) as f:
        return f.read()


@app.route("/input/node/<dataset>/<folder>/<id>", methods=['GET'])
def inode(dataset, folder, id):
    new_folder = f"{dataset}/{folder}"
    load_input_nodes(dataset, folder)
    global N_input
    return to_vis_network_node(N_input[new_folder][int(id)])


@app.route("/result/edges/<dataset>/<folder>", methods=['GET'])
def edges(dataset, folder):
    new_folder = f"{dataset}/{folder}"
    load_result_edges(dataset, folder)
    global E_result
    return E_result[new_folder]


@app.route("/input/edges/<dataset>/<folder>", methods=['GET'])
def iedges(dataset, folder):
    new_folder = f"{dataset}/{folder}"
    load_input_edges(dataset, folder)
    global E_input
    return E_input[new_folder]


@app.route("/result/graph/<dataset>/<folder>", methods=['GET'])
def result_graph(dataset, folder):
    with open("test.html", "r") as f:
        new_folder = f"{dataset}/{folder}"
        return f.read().replace("§", new_folder).replace('£', 'result')


@app.route('/input/graph/<dataset>/<folder>', methods=['GET'], strict_slashes=False)
def input_graph(dataset, folder):
    with open("test.html", "r") as f:
        new_folder = f"{dataset}/{folder}"
        content = f.read().replace("§", new_folder).replace('£', 'input')
        pos = content.find("<div id=\"title\">")
        result = content[:pos] + parsers.NestedTables.generate_morphism_html(os.path.join("/home/fox/PycharmProjects/news-crawler2/visualiser/src/results", dataset, "data"),
                                                                             folder) + content[pos:]
        return result  # f.read().replace("§", folder).replace('£','input')


# @app.post("/renderConfusionMatrix")
# def get_body(request: Request):
#     """
#     :param request: json request, for example, given a file result.json
#     {
#     "similarity_matrix": [[1,0,0],[0,1,0],[0,0,1]],
#     "sentences": ["a","b","c"]
#     }
#
#     :return: Returns the HTML rendering of this confusion matrix. If you fire the
#     request with the following command:
#
#     curl -X POST -H "Content-Type: application/json" -d @result.json http://127.0.0.1:9999/renderConfusionMatrix > test.html
#
#     you will then obtain the plot in an HTML rendering, quite simplistically.
#     """
#     payload = await request.json()
#     nd_a = np.array(payload["similarity_matrix"])
#     df = pd.DataFrame(nd_a, index=list(payload["sentences"]), columns=list(payload["sentences"]))
#     hm = sns.heatmap(data=df,
#                      annot=True)
#     fig = hm.get_figure()
#     html_content = "<html><body>"+html_base64_image(fig)+"</body></html>"
#     return HTMLResponse(content=html_content, status_code=200)


# if __name__ == '__main__':
#     uvicorn.run("main:app", port=9999, workers=1,
#                 reload=True,
#                 reload_includes=["*.json", "*.ncsv"],
#                 reload_dirs=["./data", "./data/0"])

# # create app
# # app = dash.Dash()
# if __name__ == '__main__':
#     f = deserialize_gsm_file("data/output/result.json")
#     Model = [gsm_object(id=0,ell=["label"],xi=["value"],properties={"key":"value"},phi=[phi(0,"content",1,0)]),
#              gsm_object(id=1,ell=["etichetta"],xi=["valore"],properties={"proprietà":"valore"})]
#     s = to_vis_nodes(Model)
#     p = to_vis_network_phi(Model)
#     print(serialize_gsm_model(Model))
#     print('serialized:', json.dumps(s))
#     print('serialized:', json.dumps(p))
#
#     # serialized: {'boxes': [{'maxclass': 'newobj'}, {'maxclass': 'message'}, {'maxclass': 'int'}]}
#
#     # d2 = deserialize_gsm_model(s)
#     # print('deserialized:', d2)
#     #parsers.NestedTables.generate_morphism_html(sys.argv[1])



if __name__ == '__main__':
    app.run()
