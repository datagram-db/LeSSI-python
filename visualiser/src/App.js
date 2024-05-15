import React, { useState, useEffect } from 'react';
import './App.css';
import './fonts/index.css'
import {ConfusionMatrix} from "react-confusion-matrix";

// Data
import {
  CatSimIdeasDataGraphsSimplistic,
  simIdeasDataGraphsSimplistic,
  Log,
  CatSimMPNETData,
  CatSimL6Data,
  CatSimRobertaData,
  NewcastleSimIdeasDataGraphsSimplistic,
  NewcastleSimL6Data,
  NewcastleSimMPNETData,
  NewcastleSimRobertaData,
  ABSimIdeasDataGraphsSimplistic,
  simL6Data,
  simMPNETData,
  simRobertaData,
  ABSimL6Data,
  ABSimMPNETData,
  ABSimRobertaData,
  CatSimIdeasDataGraphsLogical, CatSimIdeasDataLogicLogical, ABSimIdeasDataGraphsLogical, ABSimIdeasDataLogicLogical
} from './results';
import {elementToSVG, inlineResources} from "dom-to-svg";

function App() {
  // Config
  const [running, setRunning] = useState(false);
  const [selectedGraphUrl, setSelectedGraphUrl] = useState("")

  // Sentences
  const [inputSentences, setInputSentences] = useState(['', '', '', '']) // Sentences from user input
  const [loadedSentences, setLoadedSentences] = useState(['']) // Sentences within results section
  const [resultDescription, setResultDescription] = useState(<div></div>)

  // Flask
  const [similarity, setSimilarity] = useState("IDEAS24_graphs") // Which similarity measure to pass to Flask
  const [rewriting, setRewriting] = useState("simplistic");
  const [transformer, setTransformer] = useState("all-MiniLM-L6-v2") // Which similarity measure to pass to Flask
  const [outputText, setOutputText] = useState(['']) // Log text
  const [directory, setDirectory] = useState('')

  // Results
  const [IDEASGraphsSimplisticResults, setIDEASGraphsSimplisticResults] = useState(<div></div>);
  const [IDEASGraphsLogicalResults, setIDEASGraphsLogicalResults] = useState(<div></div>);
  const [IDEASLogicLogicalResults, setIDEASLogicLogicalResults] = useState(<div></div>);

  const [IDEASGraphsSimplisticMatrix, setIDEASGraphsSimplisticMatrix] = useState(<ConfusionMatrix data={[]} labels={[]} />)
  const [IDEASGraphsLogicalMatrix, setIDEASGraphsLogicalMatrix] = useState(<ConfusionMatrix data={[]} labels={[]} />)
  const [IDEASLogicalLogicMatrix, setIDEASLogicalLogicMatrix] = useState(<ConfusionMatrix data={[]} labels={[]} />)
  const [L6Matrix, setL6Matrix] = useState(<ConfusionMatrix data={[]} labels={[]} />)
  const [MPNETMatrix, setMPNETMatrix] = useState(<ConfusionMatrix data={[]} labels={[]} />)
  // const [RobertaMatrix, setRobertaMatrix] = useState(<ConfusionMatrix data={[]} labels={[]} />)

  const inputs = inputSentences.map((v, i) =>
    <div>
      <input key={i} defaultValue={v} onInput={(e) => {
        inputSentences[i] = e.target.value;
        e.target.defaultValue = e.target.value;
      }}/>
    </div>
  )

  useEffect(() => {
    // Clear sentences
    if (inputSentences.length === 0) {
      setInputSentences(['', '', '', ''])
    }
  }, [inputSentences]);

  useEffect(() => {
    if (!running) {
      // if (JSON.stringify(simIdeasData.sentences) === JSON.stringify(sim.sentences)) {
      //   // loadResult(simIdeasData.sentences, simIdeasData, simSTData)
      // } else {
        let empty = {"similarity_matrix": [], "sentences": []};
        if (similarity === "IDEAS24_graphs") {
          // loadResult(simIdeasData.sentences, simIdeasData, simL6Data, simMPNETData, simRobertaData)
        } else if (similarity === "SentenceTransformer" && transformer === "all-MiniLM-L6-v2") {

        } else if (similarity === "SentenceTransformer" && transformer === "all-mpnet-base-v2") {

        } else if (similarity === "SentenceTransformer" && transformer === "paraphrase-multilingual-MiniLM-L12-v2") {

        }

      // }
    }
  }, [running, simIdeasDataGraphsSimplistic]);

  useEffect(() => {
    if (running && !outputText.includes("Finished")) {
      printLog()
    }
  }, [running, outputText, Log]);

  function printLog() {
    setTimeout(() => {
      fetch('http://localhost:5000/log', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      }).then((r) => {
        r.json().then((p) => {
          let text = p.log
          console.log(text)
          console.log(outputText)
          if (!outputText.includes(text)) {
            updateArray(outputText, setOutputText, text)
            console.log(outputText)
            let logDiv = document.getElementsByClassName('log')[0]
            logDiv.scrollTop = logDiv.scrollHeight
          }
        })
      })
    }, 250)
  }

  const updateArray = (array, setArray, value) => {
    setArray(array => [...array, value])
  }

  function changeNumberOfSentence(increase) {
    if (increase) {
      setInputSentences(inputSentences => [...inputSentences, ''])
    } else {
        setInputSentences(inputSentences.slice(0, -1))
    }
  }

  function submitSentences() {
    setRunning(true);
    setOutputText([''])
    setLoadedSentences(inputSentences)
    updateArray(outputText, setOutputText, "Loading...")
    // setOutputText("Loading...\n")
    // setMatrix(<ConfusionMatrix data={[]} labels={[]} />)
    let tempSentences = inputSentences
    fetch('http://localhost:5000/sentences', {
      // mode: 'no-cors',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        'sentences': tempSentences,
        'config': {
          'sentences': tempSentences,
          'similarity': similarity,
          'HuggingFace': `sentence-transformers/${transformer}`,
          'should_generate_final_stanza_db': true,
          'should_load_handwritten_sentences': true,
          'should_run_datagram_db': true,
          'web_dir': `/home/fox/PycharmProjects/news-crawler2/visualiser/src/results/${directory}`
        }
      })
    }).then(response => {
      console.log(response)
      if (response.ok) {
        updateArray(outputText, setOutputText, "Successfully calculated " + similarity + " similarity")
        setRunning(false)
      }
    }).catch(err => {
      setOutputText([err])
      setRunning(false)
    })
  }

  function loadResult(sentences, ideasGraphsSimplistic, ideasGraphsLogical, ideasLogicLogical, l6Data, mpnetData, path = 'dataset/') {
    // let desc = <div></div>;
    // if (sentences.includes("There is traffic in the Newcastle city centre")) {
    //   desc = <div>
    //     In this example, BERT seems to evaluate that <i>'There is traffic in Newcastle but not in the city centre'</i> is <b>90% similar</b> to <i>'There is traffic in Newcastle city centre'</i>, and
    //     in fact does this for all opposing sentences. Whereas our approach evaluates a much lower similarity, suggesting a correlation but not a strong one.
    //   </div>
    //   setResultDescription(desc);
    // } else if (sentences.includes("There is traffic in Newcastle city centre")) {
    //   desc = <div>
    //     Need to write this
    //   </div>
    //   setResultDescription(desc);
    // }
    // setResultDescription(desc);


    setSelectedGraphUrl('')
    let results = sentences.map((v, i) =>
      <div key={i} className={'result'}>
        <div>
          <p>{v}</p>
        </div>
        <div>
          <button onClick={() => {
            setSelectedGraphUrl(`http://localhost:5000/input/graph/${path}${i}`)
          }}>INPUT
          </button>
          <button className={'linkBtn'} onClick={() => {
            window.open(`http://localhost:5000/input/graph/${path}${i}`)
          }}>🌐
          </button>
          <button onClick={() => {
            setSelectedGraphUrl(`http://localhost:5000/result/graph/${path}${i}`)
          }}>RESULT
          </button>
          <button className={'linkBtn'} onClick={() => {
            window.open(`http://localhost:5000/result/graph/${path}${i}`)
          }}>🌐
          </button>
        </div>
      </div>)

    // Round matricies
    let tempIData = roundMatrix(ideasGraphsSimplistic)
    let tempI2Data = roundMatrix(ideasGraphsLogical)
    let tempI3Data = roundMatrix(ideasLogicLogical)
    let tempL6Data = roundMatrix(l6Data)
    let tempMPNETData = roundMatrix(mpnetData)
    // let tempRobertaData = roundMatrix(robertaData, 4)

    const numbers = Array.from({ length: tempIData.sentences.length }, (_, index) => index + 1);

    setIDEASGraphsSimplisticResults(results)
    setIDEASGraphsSimplisticMatrix(<ConfusionMatrix
      data={tempIData.similarity_matrix}
      labels={numbers}
    />)
    setIDEASGraphsLogicalMatrix(<ConfusionMatrix
      data={tempI2Data.similarity_matrix}
      labels={numbers}
    />)
    setIDEASLogicalLogicMatrix(<ConfusionMatrix
      data={tempI3Data.similarity_matrix}
      labels={numbers}
    />)
    setL6Matrix(<ConfusionMatrix
      data={tempL6Data.similarity_matrix}
      labels={numbers}
    />)
    setMPNETMatrix(<ConfusionMatrix
      data={tempMPNETData.similarity_matrix}
      labels={numbers}
    />)
    // setRobertaMatrix(<ConfusionMatrix
    //   data={tempRobertaData.similarity_matrix}
    //   labels={numbers}
    // />)

    setLoadedSentences(sentences)
  }

  function roundMatrix(data, dp = 2) {
    for (let i = 0; i < data.similarity_matrix.length; i++) {
      let n = data.similarity_matrix[i]
      for (let j = 0; j < n.length; j++) {
        let n2 = parseFloat(n[j])
        data.similarity_matrix[i][j] = n2.toFixed(dp)
      }
    }
    return data;
  }

  const ExampleButton = (props) => {
    let name = props.name;
    let ideasGraphsSimplistic = props.ideasGraphsSimplistic;
    let ideasGraphsLogical = props.ideasGraphsLogical;
    let ideasLogicLogical = props.ideasLogicLogical;
    let l6Data = props.l6Data;
    let mpnetData = props.mpnetData;
    // let robertaData = props.robertaData;
    let path = props.path;
    let style = props.newStyle;

    return <button className={'buttonToolTip'} style={{
      backgroundColor: (loadedSentences === ideasGraphsSimplistic.sentences ? '#5bae38' : '')
    }} onClick={() => {
      loadResult(ideasGraphsSimplistic.sentences, ideasGraphsSimplistic, ideasGraphsLogical, ideasLogicLogical, l6Data, mpnetData, path);
      setInputSentences(ideasGraphsSimplistic.sentences)
      setDirectory(path)
    }}>{name}
      <span className={'toolTipText'} style={style}>
        {ideasGraphsSimplistic.sentences.map((v, i) => {
          return (i !== ideasGraphsSimplistic.sentences.length - 1) ? `[${i + 1}] ${v}\n\n` : `[${i + 1}] ${v}`
        })}
      </span>
    </button>
  }

  Number.prototype.countDecimals = function () {
    if(Math.floor(this.valueOf()) === this.valueOf()) return 0;
    return this.toString().split(".")[1].length || 0;
  }

  const oldTest = [
    'There is traffic in Newcastle city centre',
    'There is traffic in Newcastle',
    'There is no traffic in Newcastle',
    'There is traffic in Newcastle but not in the city centre'
  ]

  return (
    <div className="App">
      <div className={'innerWrapper'}>
        <div className={'leftSide'}>
          <h1>Comparison of Similarity Metrics Visualisation</h1>
          <div>
            <i><b>Authors:</b> Oliver R. Fox; Giacomo Bergami</i>
          </div>
          <div>
            <h2>Examples</h2>
            <div className={'description'}>
              Below are some pre-calculated examples that demonstrate the limitations of existing, training-based metrics
              that our proposed approach improves upon.
            </div>
            <div className={'configButtons'}>
              <ExampleButton name={'CAT AND MICE'} ideasGraphsSimplistic={CatSimIdeasDataGraphsSimplistic} ideasGraphsLogical={CatSimIdeasDataGraphsLogical} ideasLogicLogical={CatSimIdeasDataLogicLogical} l6Data={CatSimL6Data} mpnetData={CatSimMPNETData} path={'cat/'} newStyle={{marginLeft: '-35px'}}/>
              <ExampleButton name={'NEWCASTLE TRAFFIC'} ideasGraphsSimplistic={NewcastleSimIdeasDataGraphsSimplistic} l6Data={NewcastleSimL6Data} mpnetData={NewcastleSimMPNETData} path={'newcastle/'} />
              <ExampleButton name={'ALICE AND BOB'} ideasGraphsSimplistic={ABSimIdeasDataGraphsSimplistic} ideasGraphsLogical={ABSimIdeasDataGraphsLogical} ideasLogicLogical={ABSimIdeasDataLogicLogical} l6Data={ABSimL6Data} mpnetData={ABSimMPNETData} path={'ab/'} />
              <ExampleButton name={'PREVIOUS RESULTS'} ideasGraphsSimplistic={simIdeasDataGraphsSimplistic} l6Data={simL6Data} mpnetData={simMPNETData} path={''} newStyle={{marginLeft: '-175px'}} />
              </div>

              {/*<h2>Config</h2>*/}
              {/*<div>*/}


              {/*</div>*/}
            </div>

            <div className={'sentenceInputs'}>
              <div className={'sentenceHeader'}>
                <h2>Sentences</h2>
                <button onClick={() => changeNumberOfSentence(false)}>-</button>
                <button onClick={() => changeNumberOfSentence(true)}>+</button>
                <button style={{width: '65px', borderRadius: '10px', backgroundColor: '#7b2020'}} onClick={() => {
                  setInputSentences([])
                }}>CLEAR
                </button>
              </div>
              <div className={'description'}>
                Below you can input your own sentences, and use either our proposed approach or a <div className={'buttonToolTip'} style={{display: 'inline'}}>
                  'BERT'
                  <span style={{marginLeft: '-100px'}} className={'toolTipText'}>
                    <i>"BERTScore leverages the pre-trained contextual embeddings from BERT and matches words in candidate
                      and reference sentences by cosine similarity."</i> <a style={{color: '#55aded'}} href={"https://huggingface.co/spaces/evaluate-metric/bertscore"}>[ref]</a>
                  </span>
                </div> similarity
                measure
                to display a confusion matrix for the given input sentences.
              </div>
              {inputs}
            </div>

            <h2>Similarity Metric</h2>
            <div className={'description'}>
              Below gives options for our 'proposed' non-training-based approach, using graph grammars and graph matching techniques; as
              well as the training-based 'BERT' similarity measure.
            </div>
          <div className={'simBtns'}>
            <button style={{
              backgroundColor: ('IDEAS24_graphs' === similarity && 'simplistic' === rewriting) ? '#5bae38' : '#3c3c3c',
              color: 'IDEAS24_graphs' === similarity ? '' : '#6d6d6d'
            }} onClick={() => {
              setSimilarity('IDEAS24_graphs')
              setRewriting('simplistic')
              setTransformer('all-MiniLM-L6-v2')
            }}>SIMPLISTIC GRAPHS
            </button>
            <button style={{
              backgroundColor: ('IDEAS24_graphs' === similarity && 'logical' === rewriting) ? '#5bae38' : '#3c3c3c',
              color: 'IDEAS24_graphs' === similarity ? '' : '#6d6d6d'
            }} onClick={() => {
              setSimilarity('IDEAS24_graphs')
              setRewriting('logical')
              setTransformer('all-MiniLM-L6-v2')
            }}>SIMPLISTIC LOGIC
            </button>
            <button style={{
              backgroundColor: ('IDEAS24_logic' === similarity && 'logical' === rewriting) ? '#5bae38' : '#3c3c3c',
              color: 'IDEAS24_graphs' === similarity ? '' : '#6d6d6d'
            }} onClick={() => {
              setSimilarity('IDEAS24_logic')
              setRewriting('logical')
              setTransformer('all-MiniLM-L6-v2')
            }}>LOGICAL LOGIC
            </button>
            <button style={{
              backgroundColor: (similarity === "SentenceTransformer" && 'all-MiniLM-L6-v2' === transformer) ? '#5bae38' : '#3c3c3c',
              color: 'all-MiniLM-L6-v2' === transformer ? '' : '#6d6d6d'
            }} onClick={() => {
              setSimilarity('SentenceTransformer')
              setTransformer('all-MiniLM-L6-v2')
            }}>all-MiniLM-L6-v2
            </button>
            <button style={{
              backgroundColor: 'all-mpnet-base-v2' === transformer ? '#5bae38' : '#3c3c3c',
              color: 'all-mpnet-base-v2' === transformer ? '' : '#6d6d6d'
            }} onClick={() => {
              setSimilarity('SentenceTransformer')
              setTransformer('all-mpnet-base-v2')
            }}>all-mpnet-base-v2
            </button>
            {/*<button style={{*/}
            {/*  backgroundColor: 'all-roberta-large-v1' === transformer ? '#5bae38' : '#3c3c3c',*/}
            {/*  color: 'all-roberta-large-v1' === transformer ? '' : '#6d6d6d'*/}
            {/*}} onClick={() => {*/}
            {/*  setSimilarity('SentenceTransformer')*/}
            {/*  setTransformer('all-roberta-large-v1')*/}
            {/*}}>all-roberta-large-v1*/}
            {/*</button>*/}
          </div>
          <br/>
          <button className={'runBtn'} onClick={submitSentences}>RUN</button>
          <h2>Log</h2>
          <div className={'log'}>
            {outputText.map((v, i) => {
              return <div key={i}>{v}</div>
            })}
          </div>
        </div>

        {/* Download SVG */}
        {/*<button onClick={async () => {*/}
        {/*  const svgDocument = elementToSVG(document.querySelector('.resultsContainer'))*/}
        {/*  await inlineResources(svgDocument.documentElement)*/}

        {/*  // Get SVG string*/}
        {/*  const svgString = new XMLSerializer().serializeToString(svgDocument)*/}
        {/*  console.log(svgString)*/}
        {/*}}></button>*/}


        <div className={'rightSide'}>
          <h1>Results</h1>
          <div>
            {resultDescription}
          </div>
          <div className={'resultsContainer'} style={{backgroundColor:"white"}}>
            <div className={'resultsInnerDiv'}>
              <div>
                <h3 className={'resultTitle'}>Graphs Simplistic</h3>
                <div>
                  {IDEASGraphsSimplisticMatrix}
                </div>
              </div>
              <div>
                <h3 className={'resultTitle'}>Graphs with Logic</h3>
                <div>
                  {IDEASGraphsLogicalMatrix}
                </div>
              </div>
              <div>
                <h3 className={'resultTitle'}>Logical Representation</h3>
                <div>
                  {IDEASLogicalLogicMatrix}
                </div>
              </div>
            </div>
            <div className={'resultsInnerDiv'}>
              <div>
                <h3 className={'resultTitle'}>all-MiniLM-L6-v2</h3>
                <div>
                  {L6Matrix}
                </div>
              </div>
              <div>
                <h3 className={'resultTitle'}>all-mpnet-base-v2</h3>
                <div>
                  {MPNETMatrix}
                </div>
              </div>
            </div>
          </div>

          <div className={'resultsInnerDiv'}>

            {/*<div>*/}
            {/*  <h3 className={'resultTitle'}>all-roberta-Large-v1</h3>*/}
            {/*  <div>*/}
            {/*    {RobertaMatrix}*/}
            {/*  </div>*/}
            {/*</div>*/}
          </div>

          <div>
            <h2>Sentences</h2>
            <div className={'resultSentences'}>
              {IDEASGraphsSimplisticResults}
            </div>

            {selectedGraphUrl !== "" ?
              <div>
                <br/>
                <h3>Generalised Semistructured Model
                  (GSM) {selectedGraphUrl.includes('input') ? 'input' : 'result'} graph</h3>
                <div>
                  This graph has been rewritten on the given sentence in order to feed in to our similarity pipeline.
                </div>
                <iframe src={selectedGraphUrl} className={'gsmGraphWindow'} title="GSM Graph"></iframe>
              </div>
              :
              <div></div>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;