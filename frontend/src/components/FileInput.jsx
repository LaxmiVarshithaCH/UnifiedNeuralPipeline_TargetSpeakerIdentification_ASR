export default function FileInput({ label, onChange }) {
  return (
    <div className="card">
      <strong>{label}</strong><br/><br/>
      <input 
        type="file"
        accept="audio/*"
        onChange={(e) => onChange(e.target.files[0])}
      />
    </div>
  );
}
