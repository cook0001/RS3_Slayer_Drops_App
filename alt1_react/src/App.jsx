import { useState, useEffect } from 'react';
import * as chatboxModule from "alt1/chatbox";
import './App.css';

// Safely extract the ChatBoxReader constructor
let ChatBoxReader = chatboxModule;
while (typeof ChatBoxReader !== 'function' && ChatBoxReader.default) {
  ChatBoxReader = ChatBoxReader.default;
}
const reader = new ChatBoxReader();

function App() {
  const [drops, setDrops] = useState([]);
  const [session, setSession] = useState({});
  const [totalVal, setTotalVal] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [info, setInfo] = useState(null);
  const [gphr, setGphr] = useState(0);
  const [startTime, setStartTime] = useState(null);
  const [loading, setLoading] = useState(false);
  const [paused, setPaused] = useState(false);
  const [sortOption, setSortOption] = useState('value-desc');
  const [dialog, setDialog] = useState(null);
  
  // Alt1 States
  const [alt1Active, setAlt1Active] = useState(false);
  const [chatboxFound, setChatboxFound] = useState(false);
  const [hasPermissions, setHasPermissions] = useState(true);

  // Load session from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('rs3_slayer_session');
    if (saved) {
      try {
        const data = JSON.parse(saved);
        setSession(data.session || {});
        setTotalVal(data.totalVal || 0);
        setStartTime(data.startTime || null);
        setDrops(data.drops || []);
        setInfo(data.info || null);
      } catch (e) {
        console.error("Failed to load session", e);
      }
    }
  }, []);

  // Save session to localStorage
  useEffect(() => {
    if (Object.keys(session).length > 0 || drops.length > 0) {
      localStorage.setItem('rs3_slayer_session', JSON.stringify({
        session, totalVal, startTime, drops, info
      }));
    }
  }, [session, totalVal, startTime, drops, info]);

  // Alt1 Initialization and Loop
  useEffect(() => {
    if (window.alt1) {
      setAlt1Active(true);
      
      // Check permissions
      if (!window.alt1.permissionPixel) {
        setHasPermissions(false);
      }

      const interval = setInterval(() => {
        if (paused || !hasPermissions) return;

        if (!reader.pos) {
          const found = reader.find();
          if (found) setChatboxFound(true);
          return;
        }
        
        let lines = reader.read();
        if (lines) {
          lines.forEach(line => {
            const text = line.text.toLowerCase();
            if (text.includes("drop:") || text.includes("loot:")) {
              const itemName = text.split(":").pop().trim().toLowerCase();
              const match = drops.find(d => itemName.includes(d.item.toLowerCase()));
              if (match) addDrop(match);
            }
          });
        }
      }, 500);
      return () => clearInterval(interval);
    }
  }, [drops, paused, hasPermissions]);

  // GP/HR Timer
  useEffect(() => {
    if (startTime && !paused) {
      const timer = setInterval(() => {
        const elapsed = (Date.now() - startTime) / 1000;
        setGphr(elapsed > 0 ? (totalVal / (elapsed / 3600)) : 0);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [startTime, totalVal, paused]);

  // Search Autocomplete
  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (searchTerm.length >= 3) {
        try {
          const res = await fetch(`https://runescape.wiki/api.php?action=opensearch&search=${encodeURIComponent(searchTerm)}&limit=5&format=json&origin=*`);
          const data = await res.json();
          setSuggestions(data[1] || []);
        } catch (e) {
          console.error("Autocomplete failed", e);
        }
      } else {
        setSuggestions([]);
      }
    }, 300);
    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm]);

  const parsePrice = (str) => {
    let clean = str.replace(/,/g, '').replace('Not sold', '0');
    let matches = clean.match(/\d+/g);
    if (!matches) return 0;
    let sum = matches.reduce((a, b) => parseInt(a) + parseInt(b), 0);
    return Math.floor(sum / matches.length);
  };

  const fetchLivePrices = async (items) => {
    try {
      const names = items.map(d => d.item).join('|');
      const res = await fetch(`https://api.weirdgloop.org/exchange/history/rs/latest?name=${encodeURIComponent(names)}`);
      const data = await res.json();
      
      return items.map(d => {
        if (data[d.item] && data[d.item].price) {
          return { ...d, price: data[d.item].price };
        }
        return d;
      });
    } catch (e) {
      console.error("Failed to fetch live prices", e);
      return items;
    }
  };

  const executeSearch = async (term) => {
    if (!term) return;
    setSearchTerm(term);
    setSuggestions([]);
    setLoading(true);
    
    try {
      const res = await fetch(`https://runescape.wiki/api.php?action=parse&page=${encodeURIComponent(term.replace(/ /g, '_'))}&format=json&origin=*`);
      const data = await res.json();
      if (data.error) {
        setDialog({ title: "Search Error", message: "Monster not found on Wiki." });
        setLoading(false);
        return;
      }
      
      const parser = new DOMParser();
      const doc = parser.parseFromString(data.parse.text['*'], "text/html");
      
      let newDrops = [];
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

      // Fetch live prices to overwrite wiki static prices
      if (newDrops.length > 0) {
        newDrops = await fetchLivePrices(newDrops);
      }
      
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
      setDialog({ title: "Error", message: "Error fetching Wiki." });
    }
    setLoading(false);
  };

  const addDrop = (drop) => {
    setStartTime(prev => prev || Date.now());
    setSession(prev => ({
      ...prev,
      [drop.item]: (prev[drop.item] || 0) + 1
    }));
    setTotalVal(v => v + drop.price);
  };

  const resetSession = () => {
    setDialog({
      title: "Reset Session",
      message: "Are you sure you want to reset your tracking session?",
      isConfirm: true,
      onConfirm: () => {
        setSession({});
        setTotalVal(0);
        setStartTime(null);
        setGphr(0);
        localStorage.removeItem('rs3_slayer_session');
        setDialog(null);
      }
    });
  };

  const requestPermissions = () => {
    setDialog({
      title: "Missing Permissions",
      message: "Alt1 is missing pixel permissions.\n\n1. Click the wrench icon in the top right of this Alt1 window.\n2. Go to the Permissions tab.\n3. Check the box for 'Pixel' reading.\n4. Reload the app."
    });
  };

  // Sorting Logic
  const sortedDrops = [...drops].sort((a, b) => {
    if (sortOption === 'value-desc') return b.price - a.price;
    if (sortOption === 'value-asc') return a.price - b.price;
    if (sortOption === 'name-asc') return a.item.localeCompare(b.item);
    return 0;
  });

  return (
    <div className="App">
      <header>
        <div className="search-container">
          <div className="search-bar">
            <input 
              value={searchTerm} 
              onChange={e => setSearchTerm(e.target.value)} 
              placeholder="Monster Name..." 
              onKeyDown={e => e.key === 'Enter' && executeSearch(searchTerm)}
            />
            <button onClick={() => executeSearch(searchTerm)}>Search</button>
          </div>
          {suggestions.length > 0 && (
            <div className="suggestions">
              {suggestions.map((sug, i) => (
                <div key={i} className="suggestion-item" onClick={() => executeSearch(sug)}>
                  {sug}
                </div>
              ))}
            </div>
          )}
        </div>

        {alt1Active ? (
          <div className={`alt1-badge ${!hasPermissions ? 'danger' : chatboxFound ? 'success' : 'warning'}`} 
               onClick={!hasPermissions ? requestPermissions : undefined}>
            {!hasPermissions ? "❌ Missing Permissions (Click to Fix)" : 
             chatboxFound ? "🟢 Chatbox Found" : "🟡 Searching for Chatbox..."}
          </div>
        ) : (
          <a href="alt1://addapp/http://app.armstrader.store/appconfig.json" className="alt1-badge" style={{textDecoration: 'none', background: 'var(--accent)', color: 'white', borderColor: 'transparent'}}>
            ➕ Install to Alt1
          </a>
        )}
      </header>

      {info && (
        <div className="info-panel">
          <div>Weakness: <span>{info.weakness}</span></div>
          <div>Style: <span>{info.style}</span></div>
        </div>
      )}

      <div className="tracker-panel">
        <div className="tracker-header">
          <h2>Session Tracker</h2>
          <span className="gphr">{Math.floor(gphr).toLocaleString()} gp/hr</span>
        </div>
        
        <div className="total-val">{totalVal.toLocaleString()} gp</div>
        
        <div className="tracker-controls">
          <button onClick={() => setPaused(!paused)}>{paused ? "▶ Resume" : "⏸ Pause"}</button>
          <button onClick={resetSession}>🔄 Reset</button>
        </div>

        <div className="tracker-items">
          {Object.entries(session).map(([name, count]) => (
            <div key={name} className="tracker-row">
              <span className="name">{name}</span>
              <span className="qty">x{count}</span>
            </div>
          ))}
          {Object.keys(session).length === 0 && <span style={{color: 'var(--text-muted)'}}>No drops tracked yet.</span>}
        </div>
      </div>

      {drops.length > 0 && (
        <div className="controls-bar">
          <h3 style={{margin: 0}}>Loot Table</h3>
          <select className="sort-select" value={sortOption} onChange={(e) => setSortOption(e.target.value)}>
            <option value="value-desc">Highest Value</option>
            <option value="value-asc">Lowest Value</option>
            <option value="name-asc">Alphabetical (A-Z)</option>
          </select>
        </div>
      )}

      <div className="drops-list">
        {loading ? <p>Loading drops and live prices...</p> : sortedDrops.map((d, i) => (
          <div className="drop-card" key={i}>
            <img src={d.img} alt={d.item} />
            <div className="details">
              <h4>{d.item}</h4>
              <p>Qty: {d.qty} • Rarity: {d.rarity}</p>
            </div>
            <div className="price">{d.price.toLocaleString()} gp</div>
            <button className="add-btn" onClick={() => addDrop(d)} title="Manually Add">+1</button>
          </div>
        ))}
      </div>

      {dialog && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>{dialog.title}</h3>
            <p style={{ whiteSpace: "pre-wrap", color: "var(--text-muted)" }}>{dialog.message}</p>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setDialog(null)}>
                {dialog.isConfirm ? "Cancel" : "Close"}
              </button>
              {dialog.isConfirm && (
                <button className="btn-primary" onClick={dialog.onConfirm}>
                  Confirm
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
