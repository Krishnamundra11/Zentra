import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Results from "./pages/Results";
import Itinerary from "./pages/Itinerary";
import Profile from "./pages/Profile";
import Navbar from "./components/Navbar";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <Routes>
          <Route path="/"                  element={<Home />} />
          <Route path="/results/:taskId"   element={<Results />} />
          <Route path="/itinerary/:taskId" element={<Itinerary />} />
          <Route path="/profile"           element={<Profile />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
