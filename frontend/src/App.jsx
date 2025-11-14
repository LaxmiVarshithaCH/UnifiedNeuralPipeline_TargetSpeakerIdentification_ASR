import { useState } from "react";
import Navbar from "./components/Navbar";
import UploadPage from "./pages/UploadPage";
import ResultsPage from "./pages/ResultsPage";

export default function App() {
  const [results, setResults] = useState(null);

  return (
    <>
      <Navbar />

      {!results ? (
        <UploadPage setResults={setResults} />
      ) : (
        <ResultsPage results={results} />
      )}
    </>
  );
}
