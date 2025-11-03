package runtime
import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"
	"github.com/gorilla/websocket"
)
type Bridge struct {
	solver  *Solver
	upgrader websocket.Upgrader
	clients  map[*websocket.Conn]bool
	mu       sync.Mutex
}
func NewBridge(s *Solver) *Bridge {
	return &Bridge{
		solver: s,
		upgrader: websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }},
		clients: make(map[*websocket.Conn]bool),
	}
}
func (b *Bridge) ServeWS(w http.ResponseWriter, r *http.Request) {
	conn, err := b.upgrader.Upgrade(w, r, nil)
	if err != nil { log.Println("upgrade:", err); return }
	b.mu.Lock(); b.clients[conn] = true; b.mu.Unlock()
	log.Println("[Bridge] client connected")
	go func() {
		defer func() {
			conn.Close()
			b.mu.Lock(); delete(b.clients, conn); b.mu.Unlock()
			log.Println("[Bridge] client disconnected")
		}()
		for {
			time.Sleep(100 * time.Millisecond)
			st := b.solver.State()
			data,_ := json.Marshal(st)
			b.broadcast(data)
		}
	}()
}
func (b *Bridge) broadcast(data []byte) {
	b.mu.Lock(); defer b.mu.Unlock()
	for c := range b.clients {
		if err := c.WriteMessage(websocket.TextMessage, data); err != nil {
			c.Close(); delete(b.clients, c)
		}
	}
}
