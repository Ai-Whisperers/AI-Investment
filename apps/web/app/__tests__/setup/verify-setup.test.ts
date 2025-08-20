/**
 * Simple test to verify Jest setup is working
 */

describe('Jest Setup Verification', () => {
  it('should run a basic test', () => {
    expect(true).toBe(true)
  })

  it('should handle basic math', () => {
    expect(1 + 1).toBe(2)
  })

  it('should work with arrays', () => {
    const array = [1, 2, 3]
    expect(array).toHaveLength(3)
    expect(array).toContain(2)
  })

  it('should work with objects', () => {
    const obj = { name: 'test', value: 42 }
    expect(obj).toHaveProperty('name')
    expect(obj.value).toBe(42)
  })
})