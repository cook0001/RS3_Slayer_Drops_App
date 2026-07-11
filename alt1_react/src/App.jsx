import { useState, useEffect } from 'react';
import * as a1lib from "@alt1/base";
import ChatBoxReader from "@alt1/chatbox";
import './App.css';

const reader = new ChatBoxReader();

function App() {
  const [drops, setDrops] = useState([]);
  const [session, setSession] = useState({});
  const [totalVal, setTotalVal] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [info, setInfo] = useState(null);
  const [gphr, setGphr] = useState(0);
  const [startTime, setStartTime] = useState(null);
  const [loading, setLoading] = useState(false);
  const [alt1Active, setAlt1Active] = useState(false);

  useEffect(() => {
    if (window.alt1) {
      setAlt1Active(true);
      reader.read(); // Initialize reader
      const interval = setInterval(() => {
        let lines = reader.read();
        if (lines) {
          lines.forEach(line => {
            const text = line.text.toLowerCase();
            if (text.includes("drop:") || text.includes("loot:")) {
              const itemName = text.split(":").pop().trim().toLowerCase();
              autoAddDrop(itemName);
            }
          });
        }
      }, 500);
      return () => clearInterval(interval);
    }
  }, [drops]);

  useEffect(() => {
    if (startTime) {
      const timer = setInterval(() => {
        const elapsed = (Date.now() - startTime) / 1000;
        setGphr(elapsed > 0 ? (totalVal / (elapsed / 3600)) : 0);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [startTime, totalVal]);

  const autoAddDrop = (namePart) => {
    const match = drops.find(d => namePart.includes(d.item.toLowerCase()));
    if (match) addDrop(match);
  };

  const parsePrice = (str) => {
    let clean = str.replace(/,/g, '').replace('Not sold', '0');
    let matches = clean.match(/\d+/g);
    if (!matches) return 0;
    let sum = matches.reduce((a, b) => parseInt(a) + parseInt(b), 0);
    return Math.floor(sum / matches.length);
  };

  const searchWiki = async () => {
    if (!searchTerm) return;
    setLoading(true);
    try {
      const res = await fetch(`https://runescape.wiki/api.php?action=parse&page=${encodeURIComponent(searchTerm.replace(/ /g, '_'))}&format=json&origin=*`);
      const data = await res.json();
      if (data.error) {
        alert("Monster not found.");
        setLoading(false);
        return;
      }
      const parser = new DOMParser();
      const doc = parser.parseFromString(data.parse.text['*'], "text/html");
      
      const newDrops = [];
      const tables = doc.querySelectorAll('table.wikitable');
      tables.forEach(table => {
        const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim().toLowerCase());
        if (headers.includes('item') && (headers.includes('rarity') || headers.includes('drop'))) {
          const rows = table.querySelectorAll('tr');
          for (let i = 1; i < rows.length; i++) {
            const cols = rows[i].querySelectorAll('td, th');
            if (cols.length >= 5) {
              const imgTag = cols[0].querySelector('img');
              const name = cols[1].innerText.split('[')[0].trim();
              if (name && name !== "Item") {
                newDrops.push({
                  item: name,
                  qty: cols[2].innerText.trim(),
                  rarity: cols[3].innerText.split('[')[0].trim(),
                  price: parsePrice(cols[4].innerText.trim()),
                  img: imgTag ? `https://runescape.wiki${imgTag.getAttribute('src')}` : ''
                });
              }
            }
          }
        }
      });
      setDrops(newDrops);
      
      const infobox = doc.querySelector('table.infobox');
      if (infobox) {
        let weakness = "N/A", style = "N/A";
        infobox.querySelectorAll('tr').forEach(tr => {
          const th = tr.querySelector('th');
          const td = tr.querySelector('td');
          if (th && td) {
            if (th.innerText.toLowerCase().includes('weakness')) weakness = td.innerText.trim();
            if (th.innerText.toLowerCase().includes('style')) style = td.innerText.trim();
          }
        });
        setInfo({ weakness, style });
      }
    } catch (e) {
      console.error(e);
      alert("Error fetching Wiki.");
    }
    setLoading(false);
  };

  const addDrop = (drop) => {
    if (!startTime) setStartTime(Date.now());
    setSession(prev => ({
      ...prev,
      [drop.item]: (prev[drop.item] || 0) + 1
    }));
    setTotalVal(v => v + drop.price);
  };

  return (
    <div className="App">
      <header>
        <div className="search-bar">
          <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)} placeholder="Monster Name..." />
          <button onClick={searchWiki}>Search</button>
        </div>
        {alt1Active && <div className="alt1-badge">🟢 Alt1 Connected</div>}
      </header>

      {info && (
        <div className="info-panel">
          Weakness: <span>{info.weakness}</span> | Style: <span>{info.style}</span>
        </div>
      )}

      <div className="tracker-panel">
        <div className="tracker-header">
          <h2>Tracker</h2>
          <span className="gphr">{Math.floor(gphr).toLocaleString()} gp/hr</span>
        </div>
        <div className="total-val">{totalVal.toLocaleString()} gp</div>
        <div className="tracker-items">
          {Object.entries(session).map(([name, count]) => (
            <div key={name} className="tracker-row">
              <span>{name}</span>
              <span>x{count}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="drops-list">
        {loading ? <p>Loading drops...</p> : drops.map((d, i) => (
          <div className="drop-card" key={i}>
            <img src={d.img} alt={d.item} />
            <div className="details">
              <h4>{d.item}</h4>
              <p>Qty: {d.qty} • Rarity: {d.rarity}</p>
            </div>
            <div className="price">{d.price.toLocaleString()} gp</div>
            <button className="add-btn" onClick={() => addDrop(d)}>+1</button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
