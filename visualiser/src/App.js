import React, { useState, useEffect } from 'react';
import './App.css';
import './fonts/index.css'
import {ConfusionMatrix} from "react-confusion-matrix";

// Data
import { NewcastleSimIdeasData, NewcastleSimSTData, CatSimIdeasData, CatSimSTData, ABSimIdeasData, ABSimSTData, simIdeasData, simSTData, Log } from './results';

function App() {
  // Config
  const [running, setRunning] = useState(false);
  const [selectedGraphUrl, setSelectedGraphUrl] = useState("")

  // Sentences
  const [inputSentences, setInputSentences] = useState(['', '', '', '']) // Sentences from user input
  const [loadedSentences, setLoadedSentences] = useState(['']) // Sentences within results section
  const [resultDescription, setResultDescription] = useState(<div></div>)

  // Flask
  const [similarity, setSimilarity] = useState("IDEAS24") // Which similarity measure to pass to Flask
  const [outputText, setOutputText] = useState(['']) // Log text

  // Results
  const [IDEASResults, setIDEASResults] = useState(<div></div>);
  const [IDEASMatrix, setIDEASMatrix] = useState(<ConfusionMatrix data={[]} labels={[]} />)
  const [BERTResults, setBERTResults] = useState(<div></div>);
  const [BERTMatrix, setBERTMatrix] = useState(<ConfusionMatrix data={[]} labels={[]} />)

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
      if (JSON.stringify(simIdeasData.sentences) === JSON.stringify(simSTData.sentences)) {
        loadResult(simIdeasData.sentences, simIdeasData, simSTData)
      } else {
        let empty = {"similarity_matrix": [], "sentences": []};
        loadResult(similarity === "IDEAS24" ? simIdeasData.sentences : simSTData.sentences, similarity === "IDEAS24" ? simIdeasData : empty, similarity === "SentenceTransformer" ? simSTData : empty)
      }
    }
  }, [running, simIdeasData, simSTData]);

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
          'similarity': similarity,
          'should_generate_final_stanza_db': true,
          'should_load_handwritten_sentences': true,
          'should_run_datagram_db': true
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

  function loadResult(sentences, ideasData, bertData, path = 'dataset/') {
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
    let tempIData = roundMatrix(ideasData, 4)
    let tempBData = roundMatrix(bertData, 4)

    setIDEASResults(results)
    setIDEASMatrix(<ConfusionMatrix
      data={tempIData.similarity_matrix}
      labels={tempIData.sentences}
    />)
    setBERTResults(results)
    setBERTMatrix(<ConfusionMatrix
      data={tempBData.similarity_matrix}
      labels={tempBData.sentences}
    />)

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
    let ideasData = props.ideasData;
    let stData = props.stData;
    let path = props.path;
    let style = props.newStyle;

    return <button className={'buttonToolTip'} style={{
      backgroundColor: (loadedSentences === ideasData.sentences ? '#5bae38' : '')
    }} onClick={() => {
      loadResult(ideasData.sentences, ideasData, stData, path);
      setInputSentences(ideasData.sentences)
    }}>{name}
      <span className={'toolTipText'} style={style}>
        {ideasData.sentences.map((v, i) => {
          return (i !== ideasData.sentences.length - 1) ? `[${i + 1}] ${v}\n\n` : `[${i + 1}] ${v}`
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
              <ExampleButton name={'CAT AND MICE'} ideasData={CatSimIdeasData} stData={CatSimSTData} path={'cat/'} newStyle={{marginLeft: '-35px'}}/>
              <ExampleButton name={'NEWCASTLE TRAFFIC'} ideasData={NewcastleSimIdeasData} stData={NewcastleSimSTData} path={'newcastle/'} />
              <ExampleButton name={'ALICE AND BOB'} ideasData={ABSimIdeasData} stData={ABSimSTData} path={'ab/'} />
              <ExampleButton name={'PREVIOUS RESULTS'} ideasData={simIdeasData} stData={simSTData} newStyle={{marginLeft: '-175px'}} />
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
                backgroundColor: 'IDEAS24' === similarity ? '#5bae38' : '#3c3c3c',
                color: 'IDEAS24' === similarity ? '' : '#6d6d6d'
              }} onClick={() => {
                setSimilarity('IDEAS24')
              }}>PROPOSED
              </button>
              <button style={{
                backgroundColor: 'SentenceTransformer' === similarity ? '#5bae38' : '#3c3c3c',
                color: 'SentenceTransformer' === similarity ? '' : '#6d6d6d'
              }} onClick={() => {
                setSimilarity('SentenceTransformer')
              }}>BERT
              </button>
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


        <div className={'rightSide'}>
          <h1>Results</h1>
          <div>
            {resultDescription}
          </div>
          <div className={'resultsInnerDiv'}>
            <div>
              <h3>PROPOSED</h3>
              <div>
                {IDEASMatrix}
              </div>
            </div>
            <div>
              <h3>BERT</h3>
              {/*{BERTResults}*/}
              <div>
                {BERTMatrix}
              </div>
            </div>
          </div>

          <div>
            <h2>Sentences</h2>
              <div className={'resultSentences'}>
                {IDEASResults}
              </div>

              {selectedGraphUrl !== "" ?
                <div>
                  <br/>
                  <h3>Generalised Semistructured Model (GSM) {selectedGraphUrl.includes('input') ? 'input' : 'result'} graph</h3>
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