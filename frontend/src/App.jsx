import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./layouts/AppLayout";
import AdminPage from "./pages/AdminPage";
import ArchivedImagesPage from "./pages/ArchivedImagesPage";
import HomePage from "./pages/HomePage";
import LibraryPage from "./pages/LibraryPage";
import LocalityDetailPage from "./pages/LocalityDetailPage";
import LocalityFormPage from "./pages/LocalityFormPage";
import MasterAdminPage from "./pages/MasterAdminPage";
import MasterFormPage from "./pages/MasterFormPage";
import MineralDetailPage from "./pages/MineralDetailPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import SettingsPage from "./pages/SettingsPage";
import SpecimenDetailPage from "./pages/SpecimenDetailPage";
import SpecimenFormPage from "./pages/SpecimenFormPage";
import VaultPage from "./pages/VaultPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/minerals/:id" element={<MineralDetailPage />} />
        <Route path="/localities/:id" element={<LocalityDetailPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/admin/localities/new" element={<LocalityFormPage />} />
        <Route
          path="/admin/localities/:id/edit"
          element={<LocalityFormPage />}
        />
        <Route path="/admin/:resource" element={<MasterAdminPage />} />
        <Route path="/admin/:resource/new" element={<MasterFormPage />} />
        <Route
          path="/admin/:resource/:id/edit"
          element={<MasterFormPage />}
        />
        <Route path="/settings" element={<SettingsPage />} />
        <Route
          path="/settings/archived-images"
          element={<ArchivedImagesPage />}
        />
        <Route path="/vault" element={<VaultPage />} />
        <Route path="/specimens/new" element={<SpecimenFormPage />} />
        <Route path="/specimens/:id" element={<SpecimenDetailPage />} />
        <Route path="/specimens/:id/edit" element={<SpecimenFormPage />} />
        <Route
          path="/404"
          element={
            <PlaceholderPage title="404" description="ページがありません。" />
          }
        />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  );
}
