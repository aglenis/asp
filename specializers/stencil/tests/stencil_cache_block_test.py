import unittest2 as unittest
from asp.codegen.cpp_ast import *
from stencil_cache_block import *
from stencil_kernel import *

class StencilConvertASTBlockedTests(unittest.TestCase):
    def setUp(self):
        class IdentityKernel(StencilKernel):
            def kernel(self, in_grid, out_grid):
                for x in out_grid.interior_points():
                    for y in in_grid.neighbors(x, 1):
                        out_grid[x] = out_grid[x] + in_grid[y]

        self.kernel = IdentityKernel()
        self.in_grid = StencilGrid([10,10])
        self.in_grids = [self.in_grid]
        self.out_grid = StencilGrid([10,10])
        self.model = python_func_to_unrolled_model(IdentityKernel.kernel, self.in_grids, self.out_grid)

    def test_gen_loops(self):
        converter = StencilConvertASTBlocked(self.model, self.in_grids, self.out_grid)
        result = converter.gen_loops(self.model)
        wanted = """for (int x1x1 = 1; (x1x1 <= 8); x1x1 = (x1x1 + (1 * 2)))
        {
        for (int x2x2 = 1; (x2x2 <= 8); x2x2 = (x2x2 + (1 * 2)))
        for (int x1 = x1x1; (x1 <= min((x1x1 + 2),8)); x1 = (x1 + 1))
        {
        for (int x2 = x2x2; (x2 <= min((x2x2 + 2),8)); x2 = (x2 + 1))
        {
        }
        }
        }"""
        self.assertEqual(wanted.replace(' ',''), str(result[1]).replace(' ',''))


class CacheBlockerTests(unittest.TestCase):
    def test_2d(self):
        loop = For("i",
                       CNumber(0),
                       CNumber(7),
                       CNumber(1),
                       Block(contents=[For("j",
                                       CNumber(0),
                                       CNumber(3),
                                       CNumber(1),
                                       Block(contents=[Assign(CName("v"), CName("i"))]))]))
        
        
        wanted = """for (int ii = 0; (ii <= 7); ii = (ii + (1 * 2)))
        {
         for (int jj = 0; (jj <= 3); jj = (jj + (1 * 2)))
         {
          for (int i = ii; (i <= min((ii + 2),7)); i = (i + 1))
          {
           for (int j = jj; (j <= min((jj + 2),3)); j = (j + 1))
           {
            v = i;
           }
          }
         }
        }"""
        
        
        self.assertEqual(str(StencilCacheBlocker().block(loop, (2, 2))).replace(' ',''), wanted.replace(' ',''))

    def test_3d(self):
        loop = For("i",
                   CNumber(0),
                   CNumber(7),
                   CNumber(1),
                   Block(contents=[For("j",
                                       CNumber(0),
                                       CNumber(3),
                                       CNumber(1),
                                       Block(contents=[For("k",
                                                           CNumber(0),
                                                           CNumber(4),
                                                           CNumber(1),
                                                           Block(contents=[Assign(CName("v"), CName("i"))]))]))]))

        #print StencilCacheBlocker().block(loop, (2,2,3))
        wanted = """for (int ii = 0; (ii <= 7); ii = (ii + (1 * 2)))
        {
        for (int jj = 0; (jj <= 3); jj = (jj + (1 * 2)))
        {
        for (int kk = 0; (kk <= 4); kk = (kk + (1 * 3)))
        {
        for (int i = ii; (i <= min((ii + 2),7)); i = (i + 1))
        {
        for (int j = jj; (j <= min((jj + 2),3)); j = (j + 1))
        {
        for (int k = kk; (k <= min((kk + 2),4)); k = (k + 1))
        {
        v = i;
        }\n}\n}\n}\n}\n}"""
        self.assertEqual(str(StencilCacheBlocker().block(loop, (2,2,3))).replace(' ',''),
                         wanted.replace(' ', ''))


    def test_rivera_blocking(self):
        loop = For("i",
                   CNumber(0),
                   CNumber(7),
                   CNumber(1),
                   Block(contents=[For("j",
                                       CNumber(0),
                                       CNumber(3),
                                       CNumber(1),
                                       Block(contents=[For("k",
                                                           CNumber(0),
                                                           CNumber(4),
                                                           CNumber(1),
                                                           Block(contents=[Assign(CName("v"), CName("i"))]))]))]))
        #print StencilCacheBlocker().block(loop, (2,2,0))
        wanted = """for (int ii = 0; (ii <= 7); ii = (ii + (1 * 2)))
        {
        for (int jj = 0; (jj <= 3); jj = (jj + (1 * 2)))
        {
        for (int i = ii; (i <= min((ii + 2),7)); i = (i + 1))
        {
        for (int j = jj; (j <= min((jj + 2),3)); j = (j + 1))
        {
        for (int k = 0; (k <= 4); k = (k + 1))
        {
        v = i;
        }
        }
        }
        }
        }"""
        self.assertEqual(str(StencilCacheBlocker().block(loop, (2,2,0))).replace(' ',''),
                         wanted.replace(' ', ''))


def python_func_to_unrolled_model(func, in_grids, out_grid):
    python_ast = ast.parse(inspect.getsource(func).lstrip())
    model = StencilPythonFrontEnd().parse(python_ast)
    return StencilUnrollNeighborIter(model, in_grids, out_grid).run()

if __name__ == '__main__':
    unittest.main()

