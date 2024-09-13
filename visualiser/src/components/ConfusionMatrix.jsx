import { useState, useEffect } from "react";

// Components
import { Grid } from "@mui/material";

// Styles
import { TableContainer, TableCell, TableLabels, Scale } from "./styles";

export const ConfusionMatrix = (props) => {
  const { labels, data, sideBar, indexes, noLeft } = props;

  const [maxValue, setMaxValue] = useState(0);
  const [minValue, setMinValue] = useState(0);
  const [rowMaxValue, setRowMaxValue] = useState([]);

  useEffect(() => {
    let max = 0;
    let min = 0;
    let maxRow = 0;
    const tmpMaxRow = [];

    if (data.length > 0 && data[0].length > 0) {
      data.forEach((row) => {
        maxRow = 0;
        row.forEach((col) => {
          if (col > max) max = col;
          if (col > maxRow) maxRow = col;
          if (col < min) min = col;
        });
        tmpMaxRow.push(maxRow);
      });
    }
    setRowMaxValue(tmpMaxRow);
    setMaxValue(max);
    setMinValue(min);
  }, [data]);

  return (
    <Grid
      container
      sx={{
        // padding: "1rem",
        padding: "1.05rem",
      }}
    >
      <Grid item xs={12} sx={{ display: "flex", justifyContent: "center" }}>
        <TableContainer>
          <tbody>
            {data.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {/*{noLeft ? <></> : <TableLabels indexes={indexes.includes(rowIndex)}>{labels[rowIndex]}</TableLabels>}*/}
                <TableLabels indexes={indexes.includes(rowIndex)}>{labels[rowIndex]}</TableLabels>
                {row.map((col, colIndex) => {
                  return (
                    <TableCell
                      key={colIndex}
                      backgroundColor={col / rowMaxValue[colIndex]}
                      indexes={(indexes[1] === colIndex && indexes[0] === rowIndex) || (indexes[0] === colIndex && indexes[1] === rowIndex)}
                    >
                      {col}
                    </TableCell>
                  );
                })}
              </tr>
            ))}
            <tr>
              {/*{noLeft ? <></> : <td/>}*/}
              <td/>
              {labels.map((col, colIndex) => (
                <TableLabels key={colIndex} indexes={indexes.includes(colIndex)}>{col}</TableLabels>
              ))}
            </tr>
          </tbody>
        </TableContainer>
        {sideBar && (
          <>
            <Scale />
            <Grid>
              <Grid
                item
                sx={{ display: "flex", alignItems: "start", height: "50%" }}
              >
                Max: {maxValue}
              </Grid>
              <Grid
                item
                sx={{ display: "flex", alignItems: "end", height: "50%" }}
              >
                Min: {minValue}
              </Grid>
            </Grid>
          </>
        )}
      </Grid>
    </Grid>
  );
};