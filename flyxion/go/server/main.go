package main
import (
	"encoding/json"
	"log"
	"net/http"
	"time"
	"flyxion/runtime"
)
func main() {
	params := runtime.Params{Width:64, Height:64, TilesX:4, TilesY:4, DT:0.05, NoiseAmplitude:0.02, AdvectionScale:0.6, Diffusion:0.08, EntropyCoupling:0.03}
	solver := runtime.NewSolver(params)
	bridge := runtime.NewBridge(solver)
	go func() {
		tick := time.NewTicker(50 * time.Millisecond)
		for range tick.C { solver.Step(params) }
	}()
	http.HandleFunc("/state", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type","application/json")
		json.NewEncoder(w).Encode(solver.State())
	})
	http.HandleFunc("/ws", bridge.ServeWS)
	http.Handle("/", http.FileServer(http.Dir("./static")))
	log.Println("[Server] running at :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
