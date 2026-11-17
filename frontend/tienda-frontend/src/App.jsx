import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import Home from "./pages/Home.jsx";
import Section from "./pages/Section.jsx";
import Catalog from "./pages/Catalog.jsx";
import Detail from "./pages/Detail.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import NotFound from "./pages/NotFound.jsx";

// Rutas que espejan las del sitio de Django (ver frontend/README.md).
export default function App() {
  return (
    <AuthProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />

          <Route path="/login" element={<Login />} />
          <Route path="/registro" element={<Register />} />

          <Route path="/selecciones" element={<Section seccion="selecciones" />} />
          <Route path="/selecciones/:equipo" element={<Section seccion="selecciones" />} />

          <Route path="/clubes" element={<Section seccion="clubes" />} />
          <Route path="/clubes/:liga" element={<Section seccion="clubes" />} />
          <Route path="/clubes/:liga/:equipo" element={<Section seccion="clubes" />} />

          <Route path="/retro" element={<Section seccion="retro" />} />
          <Route path="/retro/:liga" element={<Section seccion="retro" />} />
          <Route path="/retro/:liga/:equipo" element={<Section seccion="retro" />} />

          <Route path="/camisetas" element={<Catalog />} />
          <Route path="/camisetas/:id" element={<Detail />} />

          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </AuthProvider>
  );
}
