"""
WebAssembly compilation setup for the mathematical engine.
Compiles pure mathematical operations for browser execution.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Dict


class WASMBuilder:
    """Builder for compiling mathematical engine to WebAssembly."""
    
    def __init__(self, source_dir: Path, output_dir: Path):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)
    
    def build_wasm(self) -> bool:
        """
        Build WebAssembly module from mathematical engine.
        Uses Pyodide for Python-to-WASM compilation.
        """
        try:
            # Configuration for WASM compilation
            build_config = {
                "entry_points": [
                    "src.financial.returns",
                    "src.prediction.trend_analysis",
                    "src.statistics.descriptive", 
                    "src.optimization.portfolio_opt",
                ],
                "exports": [
                    "simple_returns_series",
                    "linear_trend_prediction", 
                    "ensemble_trend_prediction",
                    "optimize_portfolio_weights",
                    "calculate_sharpe_ratio",
                ],
                "optimization_level": "O3",
                "memory_size": "64MB",
                "allow_memory_growth": True
            }
            
            print("🔧 Building WebAssembly module...")
            print(f"   Source: {self.source_dir}")
            print(f"   Output: {self.output_dir}")
            
            # Generate build script
            build_script = self._generate_build_script(build_config)
            
            # Write build script
            build_file = self.output_dir / "build_wasm.py"
            with open(build_file, 'w') as f:
                f.write(build_script)
            
            print(f"✅ WASM build script generated: {build_file}")
            print("📝 To compile to WASM, run:")
            print(f"   cd {self.output_dir}")
            print("   python build_wasm.py")
            
            return True
            
        except Exception as e:
            print(f"❌ WASM build failed: {e}")
            return False
    
    def _generate_build_script(self, config: Dict) -> str:
        """Generate the actual WASM build script."""
        return f'''"""
Generated WebAssembly build script for Waardhaven Math Engine.
"""

import sys
from pathlib import Path

# Add source directory to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def build_wasm():
    """Build WebAssembly module using Pyodide."""
    try:
        # Import required modules
        from pyodide_build import build_wheel
        
        print("🚀 Compiling mathematical engine to WebAssembly...")
        
        # Configuration
        config = {config}
        
        # Build process
        result = build_wheel(
            wheel_dir=Path.cwd(),
            src_dir=src_path,
            exports=config["exports"],
            optimization_level=config["optimization_level"]
        )
        
        if result:
            print("✅ WASM compilation successful!")
            print("📦 Output files:")
            for file in Path.cwd().glob("*.wasm"):
                print(f"   - {{file}}")
        else:
            print("❌ WASM compilation failed")
            
        return result
        
    except ImportError:
        print("⚠️  Pyodide not available. Install with:")
        print("   pip install pyodide-build")
        return False
    except Exception as e:
        print(f"❌ Build error: {{e}}")
        return False

if __name__ == "__main__":
    build_wasm()
'''
    
    def create_js_bindings(self) -> str:
        """Create JavaScript bindings for the WASM module."""
        bindings = '''/**
 * Waardhaven Math Engine - JavaScript Bindings
 * WebAssembly interface for mathematical operations
 */

class WaardhaveMathEngine {
    constructor(wasmModule) {
        this.module = wasmModule;
    }
    
    /**
     * Calculate simple returns from price series
     * @param {number[]} prices - Array of prices
     * @returns {number[]} - Array of returns
     */
    calculateReturns(prices) {
        return this.module.simple_returns_series(prices);
    }
    
    /**
     * Predict future prices using ensemble methods
     * @param {number[]} prices - Historical prices
     * @param {number} periods - Periods to predict
     * @returns {Array<{prediction: number, confidence: number}>}
     */
    predictTrend(prices, periods = 1) {
        return this.module.ensemble_trend_prediction(prices, periods);
    }
    
    /**
     * Optimize portfolio weights for maximum Sharpe ratio
     * @param {number[]} expectedReturns - Expected returns for each asset
     * @param {number[][]} covarianceMatrix - Covariance matrix
     * @returns {number[]} - Optimal weights
     */
    optimizePortfolio(expectedReturns, covarianceMatrix) {
        return this.module.optimize_portfolio_weights(expectedReturns, covarianceMatrix);
    }
    
    /**
     * Calculate Sharpe ratio
     * @param {number[]} returns - Return series
     * @param {number} riskFreeRate - Risk-free rate
     * @returns {number} - Sharpe ratio
     */
    calculateSharpe(returns, riskFreeRate = 0.02) {
        return this.module.calculate_sharpe_ratio(returns, riskFreeRate);
    }
}

/**
 * Load and initialize the mathematical engine
 * @returns {Promise<WaardhaveMathEngine>}
 */
export async function loadMathEngine() {
    const wasmModule = await import('./math-engine.wasm');
    await wasmModule.default();
    return new WaardhaveMathEngine(wasmModule);
}

export { WaardhaveMathEngine };
'''
        
        bindings_file = self.output_dir / "math-engine.js"
        with open(bindings_file, 'w') as f:
            f.write(bindings)
        
        return str(bindings_file)


def main():
    """Main build entry point."""
    engine_root = Path(__file__).parent.parent
    source_dir = engine_root / "src"
    output_dir = engine_root / "wasm" / "dist"
    
    builder = WASMBuilder(source_dir, output_dir)
    
    print("🧮 Waardhaven Mathematical Engine - WASM Builder")
    print("=" * 50)
    
    # Build WASM module
    success = builder.build_wasm()
    
    if success:
        # Create JavaScript bindings
        bindings_file = builder.create_js_bindings()
        print(f"✅ JavaScript bindings created: {bindings_file}")
        
        print("\n🎯 Next steps:")
        print("1. Install Pyodide: pip install pyodide-build")
        print(f"2. Run build: cd {output_dir} && python build_wasm.py")
        print("3. Import in frontend: import { loadMathEngine } from './wasm/math-engine.js'")
    
    return success


if __name__ == "__main__":
    sys.exit(0 if main() else 1)