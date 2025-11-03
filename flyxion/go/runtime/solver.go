package runtime
import (
	"math"
	"math/rand"
	"sync"
	"time"
	"flyxion/api"
)
type Solver struct {
	mu    sync.RWMutex
	state api.FieldState
	tiles []Tile
	rng   *rand.Rand
	t     float64
}
type Params struct {
	Width, Height   int
	TilesX, TilesY  int
	DT              float64
	NoiseAmplitude  float64
	AdvectionScale  float64
	Diffusion       float64
	EntropyCoupling float64
}
func NewSolver(p Params) *Solver {
	return &Solver{
		state: api.NewFieldState(p.Width, p.Height),
		tiles: Partition(p.Width, p.Height, p.TilesX, p.TilesY),
		rng:   rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}
func (s *Solver) State() api.FieldState { s.mu.RLock(); defer s.mu.RUnlock(); return s.state }
func (s *Solver) Step(p Params) {
	s.mu.Lock(); defer s.mu.Unlock()
	w, h := s.state.Width, s.state.Height
	phi := make([]float64, w*h)
	vx := make([]float64, w*h)
	vy := make([]float64, w*h)
	ent := make([]float64, w*h)
	for i, sm := range s.state.Samples {
		idx := sm.Y*w + sm.X
		phi[idx], vx[idx], vy[idx], ent[idx] = sm.Phi, sm.Vx, sm.Vy, sm.S
	}
	var wg sync.WaitGroup
	for _, tile := range s.tiles {
		wg.Add(1)
		go func(tl Tile) {
			defer wg.Done()
			for y := tl.Y0; y < tl.Y1; y++ {
				for x := tl.X0; x < tl.X1; x++ {
					i := y*w + x
					acc := phi[i]*(1-4*p.Diffusion)
					if x>0 { acc += p.Diffusion*phi[i-1] }
					if x<w-1 { acc += p.Diffusion*phi[i+1] }
					if y>0 { acc += p.Diffusion*phi[i-w] }
					if y<h-1 { acc += p.Diffusion*phi[i+w] }
					cx,cy := float64(x-w/2), float64(y-h/2)
					r := math.Hypot(cx,cy)+1e-6
					wx,wy := -cy/r, cx/r
					ax,ay := x-int(p.AdvectionScale*wx), y-int(p.AdvectionScale*wy)
					if ax<0 {ax=0}; if ax>=w {ax=w-1}
					if ay<0 {ay=0}; if ay>=h {ay=h-1}
					acc = 0.5*acc + 0.5*phi[ay*w+ax]
					ent[i] += p.EntropyCoupling*(1-ent[i])*p.DT
					acc += p.NoiseAmplitude*(s.rng.Float64()*2-1)
					phi[i], vx[i], vy[i] = acc, wx, wy
				}
			}
		}(tile)
	}
	wg.Wait()
	for i := range s.state.Samples {
		x,y := s.state.Samples[i].X, s.state.Samples[i].Y
		idx := y*w+x
		s.state.Samples[i].Phi, s.state.Samples[i].Vx, s.state.Samples[i].Vy, s.state.Samples[i].S =
			phi[idx], vx[idx], vy[idx], ent[idx]
	}
	s.t += p.DT
}
