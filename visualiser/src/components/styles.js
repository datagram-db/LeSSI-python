import { styled } from "@mui/system";

export const TableContainer = styled("table")({
  color: "darkslategray",
  aspectRatio: "1/1",
  tableLayout: "fixed",
});

export const TableCell = styled("td")((props) => {
  const { backgroundColor, size, indexes } = props;

  return {
    backgroundColor: `rgb(20, 146, 230, ${backgroundColor})`,
    padding: 8,
    color: backgroundColor > 0.5 && "white",
    minWidth: "30px",
    minHeigth: "30px",
    width: "50px",
    height: "50px",
    justifyContent: "center",
    alignItems: "center",
    roll: "gridcell",
    border: indexes ? "6px solid red" : "1px solid gray",
    fontSize: indexes ? "1.5rem" : "1.5rem"
  };
});

export const TableLabels = styled("td")((props) => {
  const { indexes } = props;

  return {
    minWidth: "25px",
    fontSize: '1.5rem',
    border: "1px solid gray",
    backgroundColor: indexes ? "red" : "white",
    color: indexes ? "white" : "black",
  }
});

export const Scale = styled("div")({
  minWidth: "1rem",
  height: "100%",
  background: "linear-gradient(rgb(20, 146, 230, 1),rgb(20, 146, 230, 0))",
  marginLeft: "20px",
});