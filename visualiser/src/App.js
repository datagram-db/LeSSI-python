import React, { useState, useEffect } from 'react';
import './App.css';
import {ConfusionMatrix} from "react-confusion-matrix";

import simIDEASData from './results/similarity_IDEAS24.json'
import simSTData from './results/similarity_SentenceTransformer.json'

function App() {
  // Config
  const [inputSentences, setInputSentences] = useState(['', '', '', ''])
  const [similarity, setSimilarity] = useState("IDEAS24")
  const [outputText, setOutputText] = useState('')
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
    console.log(inputSentences)
  }, [inputSentences, inputs]);

  function changeNumberOfSentence(increase) {
    if (increase) {
      setInputSentences(inputSentences => [...inputSentences, ''])
    } else {
        setInputSentences(inputSentences.slice(0, -1))
    }
  }

  function submitSentences() {
    // setResults(<div></div>)
    setOutputText("Loading...")
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
        setOutputText("Successfully calculated " + similarity + " similarity")

        const results = tempSentences.map((v, i) =>
          <div className={'result'}>
            <p>[{i}] {v}</p>
            <button onClick={() => {
              window.open(`http://localhost:9999/input/graph/${i}`)
            }}>INPUT
            </button>
            <button onClick={() => {
              window.open(`http://localhost:9999/result/graph/${i}`)
            }}>RESULT
            </button>
          </div>)

        if (similarity === "IDEAS24") {
          setIDEASResults(results)
          setIDEASMatrix(<ConfusionMatrix
            data={simIDEASData.similarity_matrix}
            labels={simIDEASData.sentences}
          />)
        } else {
          setBERTResults(results)
          setBERTMatrix(<ConfusionMatrix
            data={simSTData.similarity_matrix}
            labels={simSTData.sentences}
          />)
        }

      }
    }).catch(err => {
      setOutputText(err)
    })
  }

  return (
      <div className="App">
        <div className={'innerWrapper'}>
          <div className={'leftSide'}>
            <h1>GSM Demo</h1>
            <div>
              <h2>Config</h2>
              <div className={'configButtons'}>
                <button onClick={() => {
                  const tests = [
                    'The cat eats the mouse',
                    'The mouse is eaten by the cat',
                    'The mouse eats the cat',
                    'The cat is eaten by the mouse'
                  ]
                  setInputSentences(inputSentences.map((v, i) => {
                    return tests[i]
                  }))
                }}>CAT VALUES
                </button>
                <button onClick={() => {
                  const tests = [
                    'There is no traffic in the Newcastle city centre',
                    'There is traffic in the Newcastle city centre',
                    'There is traffic but not in the Newcastle city centre',
                    'In Newcastle, traffic is flowing'
                  ]
                  const oldTest = [
                    'There is traffic in Newcastle city centre',
                    'There is traffic in Newcastle',
                    'There is no traffic in Newcastle',
                    'There is traffic in Newcastle but not in the city centre'
                  ]
                  setInputSentences(inputSentences.map((v, i) => {
                    return tests[i]
                  }))
                }}>NEWCASTLE VALUES
                </button>
                <button onClick={() => {
                  const emptyValue = inputSentences.map((v, i) => {
                    return ''
                  })
                  setInputSentences(emptyValue)
                }}>CLEAR VALUES
                </button>
                <button onClick={() => {
                  let oldResults = inputSentences.map((v, i) =>
                    <div className={'result'}>
                      <p>[{i}] {v}</p>
                      <button onClick={() => {
                        window.open(`http://localhost:9999/input/graph/${i}`)
                      }}>INPUT
                      </button>
                      <button onClick={() => {
                        window.open(`http://localhost:9999/result/graph/${i}`)
                      }}>RESULT
                      </button>
                    </div>)

                  setIDEASResults(oldResults)
                  setIDEASMatrix(<ConfusionMatrix
                    data={simIDEASData.similarity_matrix}
                    labels={simIDEASData.sentences}
                  />)
                  setBERTResults(oldResults)
                  setBERTMatrix(<ConfusionMatrix
                    data={simSTData.similarity_matrix}
                    labels={simSTData.sentences}
                  />)
                }}>LOAD PREVIOUS RESULTS
                </button>
              </div>
              <br/><br/>

              <div>
                <b>Number of input fields ({inputSentences.length}): <br/></b>
                <button onClick={() => changeNumberOfSentence(false)}>-</button>
                <button onClick={() => changeNumberOfSentence(true)}>+</button>
              </div>
            </div>

            <div className={'sentenceInputs'}>
              <h2>Sentences</h2>
              {inputs}
            </div>
            <div>
              <button style={{backgroundColor: 'IDEAS24' === similarity ? '' : '#3c3c3c'}} onClick={() => {
                setSimilarity('IDEAS24')
              }}>IDEAS24
              </button>
              <button style={{backgroundColor: 'SentenceTransformer' === similarity ? '' : '#3c3c3c'}} onClick={() => {
                setSimilarity('SentenceTransformer')
              }}>BERT
              </button>
            </div>
            <br/>
            <button onClick={submitSentences}>SUBMIT</button>
            <h2>Log</h2>
            {outputText}
          </div>


          <div className={'rightSide'}>
            <h2>Results</h2>

            <h3>IDEAS24</h3>
            {IDEASResults}
            <div>
              {IDEASMatrix}
            </div>

            <h3>BERT</h3>
            {BERTResults}
            {BERTMatrix}

          </div>
        </div>
      </div>
  );
}

export default App;