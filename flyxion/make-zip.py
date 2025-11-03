import os
import zipfile

# Define the file structure
files = {
    "flyxion/Makefile": """# ============================================================
# Flyxion Makefile
# ============================================================
APP_NAME = flyxiond
GO_DIR   = go/server
STATIC   = static
ELM_DIR  = elm
PORT     = 8080

.PHONY: all build run clean docker docker-run

all: build

build: $(STATIC)/main.js
\tcd $(GO_DIR) && go build -o ../../$(APP_NAME)
\t@echo "[Flyxion] ✅ Build complete."

$(STATIC)/main.js:
\tcd $(ELM_DIR) && elm make src/Main.elm --optimize --output=../static/main.js

run: build
\t./$(APP_NAME)

clean:
\trm -f $(APP_NAME) $(STATIC)/main.js

docker:
\tdocker build -t flyxion:latest .

docker-run:
\tdocker run -p $(PORT):8080 flyxion:latest
""",

    "flyxion/Dockerfile": """FROM node:20-alpine AS elm-builder
WORKDIR /app
RUN npm install -g elm@0.19.1
COPY elm/ ./elm/
WORKDIR /app/elm
RUN elm make src/Main.elm --optimize --output=../static/main.js

FROM golang:1.22-alpine AS go-builder
WORKDIR /app
COPY go/ ./go/
COPY static/ ./static/
COPY --from=elm-builder /app/static/main.js ./static/main.js
WORKDIR /app/go/server
RUN go mod init flyxion || true && go mod tidy
RUN go build -o /flyxiond

FROM alpine:3.20
WORKDIR /app
COPY --from=go-builder /flyxiond .
COPY --from=go-builder /app/static ./static
EXPOSE 8080
ENV RSVP_W=64 RSVP_H=64
ENTRYPOINT ["./flyxiond"]
""",

    "flyxion/go/api/types.go": """package api
type FieldSample struct {
\tX, Y   int     `json:"x"`
\tPhi    float64 `json:"phi"`
\tVx, Vy float64 `json:"vx","vy"`
\tS      float64 `json:"s"`
}
type FieldState struct {
\tWidth, Height int           `json:"width","height"`
\tSamples       []FieldSample `json:"samples"`
}
func NewFieldState(w, h int) FieldState {
\ts := make([]FieldSample, 0, w*h)
\tfor y := 0; y < h; y++ {
\t\tfor x := 0; x < w; x++ {
\t\t\ts = append(s, FieldSample{X: x, Y: y})
\t\t}
\t}
\treturn FieldState{Width: w, Height: h, Samples: s}
}
""",

    "flyxion/go/runtime/mesh.go": """package runtime
type Tile struct{ X0, Y0, X1, Y1 int }
func Partition(width, height, tilesX, tilesY int) []Tile {
\tif tilesX < 1 { tilesX = 1 }
\tif tilesY < 1 { tilesY = 1 }
\tvar out []Tile
\twStep := (width + tilesX - 1) / tilesX
\thStep := (height + tilesY - 1) / tilesY
\tfor ty := 0; ty < tilesY; ty++ {
\t\tfor tx := 0; tx < tilesX; tx++ {
\t\t\tx0, y0 := tx*wStep, ty*hStep
\t\t\tx1, y1 := min((tx+1)*wStep, width), min((ty+1)*hStep, height)
\t\t\tout = append(out, Tile{x0, y0, x1, y1})
\t\t}
\t}
\treturn out
}
func min(a, b int) int { if a < b { return a }; return b }
""",

    "flyxion/go/runtime/solver.go": """package runtime
import (
\t"math"
\t"math/rand"
\t"sync"
\t"time"
\t"flyxion/api"
)
type Solver struct {
\tmu    sync.RWMutex
\tstate api.FieldState
\ttiles []Tile
\trng   *rand.Rand
\tt     float64
}
type Params struct {
\tWidth, Height   int
\tTilesX, TilesY  int
\tDT              float64
\tNoiseAmplitude  float64
\tAdvectionScale  float64
\tDiffusion       float64
\tEntropyCoupling float64
}
func NewSolver(p Params) *Solver {
\treturn &Solver{
\t\tstate: api.NewFieldState(p.Width, p.Height),
\t\ttiles: Partition(p.Width, p.Height, p.TilesX, p.TilesY),
\t\trng:   rand.New(rand.NewSource(time.Now().UnixNano())),
\t}
}
func (s *Solver) State() api.FieldState { s.mu.RLock(); defer s.mu.RUnlock(); return s.state }
func (s *Solver) Step(p Params) {
\ts.mu.Lock(); defer s.mu.Unlock()
\tw, h := s.state.Width, s.state.Height
\tphi := make([]float64, w*h)
\tvx := make([]float64, w*h)
\tvy := make([]float64, w*h)
\tent := make([]float64, w*h)
\tfor i, sm := range s.state.Samples {
\t\tidx := sm.Y*w + sm.X
\t\tphi[idx], vx[idx], vy[idx], ent[idx] = sm.Phi, sm.Vx, sm.Vy, sm.S
\t}
\tvar wg sync.WaitGroup
\tfor _, tile := range s.tiles {
\t\twg.Add(1)
\t\tgo func(tl Tile) {
\t\t\tdefer wg.Done()
\t\t\tfor y := tl.Y0; y < tl.Y1; y++ {
\t\t\t\tfor x := tl.X0; x < tl.X1; x++ {
\t\t\t\t\ti := y*w + x
\t\t\t\t\tacc := phi[i]*(1-4*p.Diffusion)
\t\t\t\t\tif x>0 { acc += p.Diffusion*phi[i-1] }
\t\t\t\t\tif x<w-1 { acc += p.Diffusion*phi[i+1] }
\t\t\t\t\tif y>0 { acc += p.Diffusion*phi[i-w] }
\t\t\t\t\tif y<h-1 { acc += p.Diffusion*phi[i+w] }
\t\t\t\t\tcx,cy := float64(x-w/2), float64(y-h/2)
\t\t\t\t\tr := math.Hypot(cx,cy)+1e-6
\t\t\t\t\twx,wy := -cy/r, cx/r
\t\t\t\t\tax,ay := x-int(p.AdvectionScale*wx), y-int(p.AdvectionScale*wy)
\t\t\t\t\tif ax<0 {ax=0}; if ax>=w {ax=w-1}
\t\t\t\t\tif ay<0 {ay=0}; if ay>=h {ay=h-1}
\t\t\t\t\tacc = 0.5*acc + 0.5*phi[ay*w+ax]
\t\t\t\t\tent[i] += p.EntropyCoupling*(1-ent[i])*p.DT
\t\t\t\t\tacc += p.NoiseAmplitude*(s.rng.Float64()*2-1)
\t\t\t\t\tphi[i], vx[i], vy[i] = acc, wx, wy
\t\t\t\t}
\t\t\t}
\t\t}(tile)
\t}
\twg.Wait()
\tfor i := range s.state.Samples {
\t\tx,y := s.state.Samples[i].X, s.state.Samples[i].Y
\t\tidx := y*w+x
\t\ts.state.Samples[i].Phi, s.state.Samples[i].Vx, s.state.Samples[i].Vy, s.state.Samples[i].S =
\t\t\tphi[idx], vx[idx], vy[idx], ent[idx]
\t}
\ts.t += p.DT
}
""",

    "flyxion/go/runtime/websocket_bridge.go": """package runtime
import (
\t"encoding/json"
\t"log"
\t"net/http"
\t"sync"
\t"time"
\t"github.com/gorilla/websocket"
)
type Bridge struct {
\tsolver  *Solver
\tupgrader websocket.Upgrader
\tclients  map[*websocket.Conn]bool
\tmu       sync.Mutex
}
func NewBridge(s *Solver) *Bridge {
\treturn &Bridge{
\t\tsolver: s,
\t\tupgrader: websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }},
\t\tclients: make(map[*websocket.Conn]bool),
\t}
}
func (b *Bridge) ServeWS(w http.ResponseWriter, r *http.Request) {
\tconn, err := b.upgrader.Upgrade(w, r, nil)
\tif err != nil { log.Println("upgrade:", err); return }
\tb.mu.Lock(); b.clients[conn] = true; b.mu.Unlock()
\tlog.Println("[Bridge] client connected")
\tgo func() {
\t\tdefer func() {
\t\t\tconn.Close()
\t\t\tb.mu.Lock(); delete(b.clients, conn); b.mu.Unlock()
\t\t\tlog.Println("[Bridge] client disconnected")
\t\t}()
\t\tfor {
\t\t\ttime.Sleep(100 * time.Millisecond)
\t\t\tst := b.solver.State()
\t\t\tdata,_ := json.Marshal(st)
\t\t\tb.broadcast(data)
\t\t}
\t}()
}
func (b *Bridge) broadcast(data []byte) {
\tb.mu.Lock(); defer b.mu.Unlock()
\tfor c := range b.clients {
\t\tif err := c.WriteMessage(websocket.TextMessage, data); err != nil {
\t\t\tc.Close(); delete(b.clients, c)
\t\t}
\t}
}
""",

    "flyxion/go/server/main.go": """package main
import (
\t"encoding/json"
\t"log"
\t"net/http"
\t"time"
\t"flyxion/runtime"
)
func main() {
\tparams := runtime.Params{Width:64, Height:64, TilesX:4, TilesY:4, DT:0.05, NoiseAmplitude:0.02, AdvectionScale:0.6, Diffusion:0.08, EntropyCoupling:0.03}
\tsolver := runtime.NewSolver(params)
\tbridge := runtime.NewBridge(solver)
\tgo func() {
\t\ttick := time.NewTicker(50 * time.Millisecond)
\t\tfor range tick.C { solver.Step(params) }
\t}()
\thttp.HandleFunc("/state", func(w http.ResponseWriter, r *http.Request) {
\t\tw.Header().Set("Content-Type","application/json")
\t\tjson.NewEncoder(w).Encode(solver.State())
\t})
\thttp.HandleFunc("/ws", bridge.ServeWS)
\thttp.Handle("/", http.FileServer(http.Dir("./static")))
\tlog.Println("[Server] running at :8080")
\tlog.Fatal(http.ListenAndServe(":8080", nil))
}
""",

    "flyxion/elm/src/Main.elm": """module Main exposing (main)
import Browser
import Html exposing (Html, div, text)
import Json.Decode as D
import Svg exposing (..)
import Svg.Attributes as SA
import WebSocket
import Time
type alias FieldSample = { x : Int, y : Int, phi : Float, vx : Float, vy : Float, s : Float }
type alias Model = Maybe (List FieldSample)
init _ = ( Nothing, Cmd.none )
type Msg = Tick Time.Posix | ReceiveData (Result WebSocket.Error (List FieldSample))
update msg model = case msg of
\tTick _ -> (model, Cmd.none)
\tReceiveData (Ok samples) -> (Just samples, Cmd.none)
\t_ -> (model, Cmd.none)
subscriptions _ = Sub.batch [ WebSocket.listen "ws://localhost:8080/ws" ReceiveData, Time.every 100 Tick ]
main = Browser.element { init = init, update = update, view = view, subscriptions = subscriptions }
view model = case model of
\tNothing -> div [] [ text "Connecting..." ]
\tJust samples -> svg [ SA.width "640", SA.height "640" ] (List.map cell samples)
cell s = let c = String.fromInt (round (255 * (0.5 + s.phi / 2))) in rect [ SA.x (String.fromInt (s.x * 10)), SA.y (String.fromInt (s.y * 10)), SA.width "10", SA.height "10", SA.fill ("rgb("++c++","++c++","++c++")") ] []
""",

    "flyxion/static/index.html": """<!doctype html>
<html>
<head><meta charset="utf-8"><title>RSVP Field</title></head>
<body>
  <div id="app"></div>
  <script src="main.js"></script>
  <script>Elm.Main.init({ node: document.getElementById('app') });</script>
</body>
</html>
"""
}

# Create directories and files
os.makedirs("flyxion", exist_ok=True)
for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

# Zip it
zip_filename = "/mnt/data/flyxion_demo.zip"
with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as z:
    for path in files.keys():
        z.write(path)

zip_filename

