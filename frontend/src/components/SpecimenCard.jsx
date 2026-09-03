import { Link } from "react-router-dom";

import { imageContentUrl } from "../api/client";

export default function SpecimenCard({ specimen, view = "grid" }) {
  return (
    <Link
      className={`specimen-card specimen-card--${view}`}
      to={`/specimens/${specimen.id}`}
    >
      <div className="specimen-card__image" aria-hidden="true">
        {specimen.thumbnail_image_id ? (
          <img
            alt=""
            loading="lazy"
            src={imageContentUrl(specimen.thumbnail_image_id)}
          />
        ) : (
          "NO IMAGE"
        )}
      </div>
      <div className="specimen-card__body">
        <div className="specimen-card__number">
          No. {String(specimen.specimen_no).padStart(3, "0")}
          {specimen.favorite && <span title="お気に入り"> ★</span>}
        </div>
        <h2>{specimen.specimen_name}</h2>
        <p>{specimen.mineral_names.join("、") || "鉱物未設定"}</p>
        <p>{specimen.locality?.locality_name ?? "採集地未設定"}</p>
      </div>
    </Link>
  );
}
