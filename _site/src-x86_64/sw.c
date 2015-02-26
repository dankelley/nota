#include <R.h>
#include <Rdefines.h>

void
sw_alpha_over_beta(int *n, double *pS, double *ptheta, double *pp, double *value)
{
  int i;
  for (i = 0; i < *n; i++) {
    double S = *pS++;
    double theta = *ptheta++;
    double p = *pp++;
    /*
      printf("%f %f %f\n",S,T,p);
      printf("missing? %d %d %d\n",ISNA(S),ISNA(T),ISNA(p));
    */
    if (ISNA(S) || ISNA(theta) || ISNA(p)) {
      *value++ = NA_REAL;
    } else {
      S -= 35.0;
      *value++ = (0.665157e-1 + theta * (0.170907e-1 + theta * (-0.203814e-3 + theta * (0.298357e-5 + theta * (-0.255019e-7)))))
	+ S * (
	       (0.378110e-2 + theta * (-0.846960e-4))
	       + p * (-0.164759e-6 + p * (-0.251520e-11)))
	+ S * S * (-0.678662e-5)
	+ p * (0.380374e-4 + theta * (-0.933746e-6 + theta * (0.791325e-8)))
	+ 0.512857e-12* p * p * theta *theta
	+ -0.302285e-13 * p * p * p;
    }
  }
}

void
sw_beta(int *n, double *pS, double *ptheta, double *pp, double *value)
{
  int i;
  for (i = 0; i < *n; i++) {
    double S = *pS++;
    double theta = *ptheta++;
    double p = *pp++;
    if (ISNA(S) || ISNA(theta) || ISNA(p)) {
      *value++ = NA_REAL;
    } else {
      S -= 35.0;
      *value++ =
	0.785567e-3 + theta * (-0.301985e-5 + theta * (0.555579e-7 + theta *(-0.415613e-9)))
	+ S * (-0.356603e-6 + 0.788212e-8 * theta + p * (0.408195e-10 + p * (-0.602281e-15)))
	+ S * S * (0.515032e-8)
	+ p * (-0.121555e-7 + theta * (0.192867e-9 + theta * (-0.213127e-11)))
	+ p * p * (0.176621e-12 + theta * (-0.175379e-14))
	+ p * p * p * (0.121551e-17);
    }
  }
}

void
sw_lapserate(int *n, double *pS, double *pT, double *pp, double *value)
{
  /* Fofonoff & Millard (1983 UNESCO) section 7, equation 31*/
  static double a[4] = {
    3.5803e-5, 8.5258e-6, -6.8360e-8, 6.6228e-10
  };
  static double b[2] = {
    1.8932e-6, -4.2393e-8
  };
  static double c[4] = {
    1.8741e-8, -6.7795e-10, 8.7330e-12, -5.4481e-14
  };
  static double d[2] = {
    -1.1351e-10, 2.7759e-12
  };
  static double e[3] = {
    -4.6206e-13, 1.8676e-14, -2.1687e-16
  };
  int i;
  for (i = 0; i < *n; i++) {
    double S = *pS++;
    double T = *pT++;
    double p = *pp++;
    if (ISNA(S) || ISNA(T) || ISNA(p)) {
      *value++ = NA_REAL;
    } else {
      double lf = a[0] + T * (a[1] + T * (a[2] + T * a[3]))
	+ (b[0] + b[1] * T) * (S - 35.0)
	+ (c[0] + T * (c[1] + T * (c[2] + T * c[3]))
	   + (d[0] + T * d[1]) * (S - 35.0)) * p
	+ (e[0] + T * (e[1] + T * e[2])) * p * p;
      *value++ = lf;
    }
  }
}

void
sw_rho(int *n, double *pS, double *pT, double *pp, double *value)
{
  int i;
  for (i = 0; i < *n; i++) {
    double S = *pS++;
    double T = *pT++;
    double p = *pp++;
    double rho_w, Kw, Aw, Bw, p1, S12, ro, xkst;
    if (ISNA(S) || ISNA(T) || ISNA(p)) {
      *value++ = NA_REAL;
    } else {
      rho_w = 999.842594 +
	T * (6.793952e-2 +
	     T * (-9.095290e-3 +
		  T * (1.001685e-4 +
		       T * (-1.120083e-6 + T * 6.536332e-9))));
      Kw = 19652.21
	+ T * (148.4206 +
	       T * (-2.327105 +
		    T * (1.360477e-2 - T * 5.155288e-5)));
      Aw = 3.239908 +
	T * (1.43713e-3 +
	     T * (1.16092e-4 -
		  T * 5.77905e-7));
      Bw = 8.50935e-5 +
	T * (-6.12293e-6 +
	     T * 5.2787e-8);
      p1 = 0.1 * p;
      S12 = sqrt(S);
      ro = rho_w +
	S * (8.24493e-1 +
	     T * (-4.0899e-3 +
		  T * (7.6438e-5 +
		       T * (-8.2467e-7 + T * 5.3875e-9))) +
	     S12 * (-5.72466e-3 +
		    T * (1.0227e-4 -
			 T * 1.6546e-6) +
		    S12 * 4.8314e-4));
      xkst = Kw +
	S * (54.6746 +
	     T * (-0.603459 +
		  T * (1.09987e-2 -
		       T * 6.1670e-5)) +
	     S12 * (7.944e-2 +
		    T * (1.6483e-2 +
			 T * (-5.3009e-4)))) +
	p1 * (Aw +
	      S * (2.2838e-3 +
		   T * (-1.0981e-5 +
			T * (-1.6078e-6)) +
		   S12 * (1.91075e-4)) +
	      p1 * (Bw +
		    S * (-9.9348e-7 +
			 T * (2.0816e-8 +
			      T * (9.1697e-10)))));
      *value++ = (ro / (1.0 - p1 / xkst));
    }
  }
}

void
sw_salinity(int *n, double *pC, double *pT, double *pp, double *value)
{
  int i;
  static double c[5] = {
    0.6766097, 2.00564e-2, 1.104259e-4, -6.9698e-7, 1.0031e-9
  };
  static double d[4] = {
    3.426e-2, 4.464e-4, 4.215e-1, -3.107e-3
  };
  static double e[4] = {
    2.070e-5, -6.370e-10, 3.989e-15
  };
  static double a[6] = {
    0.0080, -0.1692, 25.3851, 14.0941,	-7.0261, 2.7081
  };
  static double b[6] = {
    0.0005,	-0.0056, -0.0066, -0.0375, 0.0636, -0.0144
  };
  static double k = 0.0162;
  double rt, Rp, Rt, Rtx, del_T, del_S, S;
  double C, T, p;
  for (i = 0; i < *n; i++) {
    C = *pC++;
    T = *pT++;
    p = *pp++;
    if (ISNA(C) || ISNA(T) || ISNA(p)) {
      *value++ = NA_REAL;
    } else {
      /* Follows the UNESCO formulae of FM83, i.e.
       * Fofonoff, P. and R. C. Millard Jr, 1983. Algorithms for computation of
       * fundamental properties of seawater. \emph{Unesco Technical Papers in Marine
       * Science}, \bold{44}, 53 pp
       *
       * Test values, p9 of FM83:
       * stopifnot(all.equal.numeric(S.C.T.p(1,   15,   0), 35.000000, 1e-6))
       * stopifnot(all.equal.numeric(S.C.T.p(1.2, 20,2000), 37.245628, 1e-6))
       * stopifnot(all.equal.numeric(S.C.T.p(0.65, 5,1500), 27.995347, 1e-6))
       */
      
      /* rt = rt(T) = C(35,T,0)/C(35,15,0), eqn (3) p.7 FM83 */
      rt = c[0] + T*(c[1] + T*(c[2] + T*(c[3] + T*c[4])));
      /* Rp, eqn (4) p.8 FM83 */
      Rp = 1 + ( p * (e[0] + p * (e[1] + p * e[2]))) /
	(1 + T *(d[0] + T * d[1]) + (d[2] + T * d[3]) * C);
      Rt = C / (Rp * rt);
      /* Eqn (1) & (2) p6 and 7 FM83 */
      Rtx = sqrt(Rt);
      del_T = T - 15;
      del_S = (del_T / (1 + k * del_T) ) *
	(b[0] + (b[1] + (b[2]+ (b[3] + (b[4] + b[5]*Rtx)*Rtx)*Rtx)*Rtx)*Rtx);
      S = a[0] + (a[1] + (a[2] + (a[3] + (a[4] + a[5]*Rtx)*Rtx)*Rtx)*Rtx)*Rtx;
      S = S + del_S;
      *value++ = S;
    }
  }
}

void
sw_spice(int *n, double *pS, double *pT, double *pp, double *value)
{
  static double b[6][5] = {
    { 0.,          7.7442e-1, -5.85e-3,   -9.84e-4,   -2.06e-4},
    { 5.1655e-2,   2.034e-3,  -2.742e-4,  -8.5e-6,     1.36e-5},
    { 6.64783e-3, -2.4681e-4, -1.428e-5,   3.337e-5,   7.894e-6},
    {-5.4023e-5,   7.326e-6,   7.0036e-6, -3.0412e-6, -1.0853e-6},
    { 3.949e-7,   -3.029e-8,  -3.8209e-7,  1.0012e-7,  4.7133e-8},
    {-6.36e-10,   -1.309e-9,   6.048e-9,  -1.1409e-9, -6.676e-10}};
  int i;
  for (i = 0; i < *n; i++) {
    double S = *pS++;
    double T = *pT++;
    double p = *pp++;
    int ii, jj;
    double Sdev, S2, T2, spice;
    if (ISNA(S) || ISNA(T) || ISNA(p)) {
      *value++ = NA_REAL;
    } else {
      Sdev = (S - 35.0);
      S2 = 0.0;
      T2 = 1.0;
      spice = 0.0;
      for (ii = 0; ii < 6; ii++) {
	S2 = 1.0;
	for (jj = 0; jj < 5; jj++) {
	  spice += b[ii][jj] * T2 * S2;
	  S2 *= Sdev;
	}
	T2 *= T;
      }
      *value++ = spice;
    }
  }
}

/* Original code from Pierre Flament's website 
   http://satftp.soest.hawaii.edu/spice/spice.html
   
   Converted to a form suitable R usage in the "oce" library,
   including changing the call and making the coefficient definition
   for efficiency, by Dan Kelley 2003-jul-27.
   
   NB. pressure is ignored.
   
   License information: the following is quoted from an email
   from Pierre Flament to Dan Kelley, 
   Message-id: <3F22F951.5010505@mael.soest.hawaii.edu>
   From pflament@mael.satlab.hawaii.edu  Sat Jul 26 18:59:44 2003
   
   "I hereby tranfer all rights of use, licensing and copyright to my
   definition of "spiciness" which appeared in Progress in
   Oceanography, to Dan Kelley, with the provision that he uses,
   diseminates and relicenses it under the provision of the GNU
   licensing scheme."
   
   Pierre Flament.
*/
static double sig_0, p_ref, S, T;
void
sw_strho(double *pT, double *prho, double *pp, double *res)
{
  int strho_bisection_search (double *x, double x1, double x2, double eps, double eta);
  int bs_res;
  T = *pT;
  sig_0 = *prho;				/* target density */
  p_ref = *pp;				/* target pressure */
  *res = NA_REAL;
  if (ISNA(*pT) || ISNA(*prho) || ISNA(*pp))
    return;
  bs_res = strho_bisection_search(&S, 0.0001, 200.0, 0.00001, 0.00001);
  *res = S;
}

double
strho_f(double x)
{
  extern double p_ref, sig_0;
  void sw_rho(int *n, double *pS, double *pT, double *pp, double *res);
  double this_rho;
  int n=1;
  sw_rho(&n, &x, &T, &p_ref, &this_rho);
  /* printf(" f returning %f\n", this_rho-1000.0-sig_0); */
  return (this_rho - 1000.0 - sig_0);
}

/* bisection rootsolver
   SYNTAX
   int bis(double *x,double x1,double x2,double eps,double eta);
   DESCRIPTION: Searches for a root of f(x) over the interval [x1,x2].
   ftol = maximum allowed error in f(x)
   xresolution = maximum size of final interval bracketing  root
   RETURN VALUE
   0 if root found to within tolerance; 1 otherwise
*/
int
strho_bisection_search(double *x, double x1, double x2, double xresolution, double ftol)
{
  /* printf("in bisection_search(x=%f,  x1=%f,  x2=%f)\n",*x,x1,x2); */
  extern double strho_f(double x);
  double g1, g2, g;
  g1 = strho_f(x1);
  g2 = strho_f(x2);
  if (g1 * g2 > 0.0) {
    *x = NA_REAL;
    return 0;
  }
  /* printf("TOP of bs.  g1=%f   g2=%f\n",g1,g2); */
  while (fabs (g = strho_f (*x = (x1 + x2) / 2.0)) > ftol || fabs (x1 - x2) > xresolution) {
    /* printf("in bis loop x=%f   g=%f   g1=%f\n",*x,g,g1); */
    if (g1 * g < 0) { /* root is nearer x1 so move x2 to x */
      x2 = *x;
      g2 = g;
      /* printf("bs CASE 1.  x1=%f  x2=%f  g1=%f  g2=%f\n",x1,x2,g1,g2); */
    } else if (g2 * g < 0) { /* root is nearer x2 so move x1 to x */
      x1 = *x;
      g1 = g;
      /* printf("bs CASE 2.  x1=%f  x2=%f  g1=%f  g2=%f\n",x1,x2,g1,g2); */
    } else {	/* not bracketed BUG */
      /* printf("bs CASE 3 (not bracketed)  x1=%f  x2=%f  g1=%f  g2=%f\n",x1,x2,g1,g2);*/
      *x = NA_REAL;
      return (1); /* exact solution */
    }
  }
  return (0); 		/* converged by default */
}

void
sw_svel(int *n, double *pS, double *pT, double *pp, double *value)
{
  int i;
  for (i = 0; i < *n; i++) {
    double S = *pS++;
    double T = *pT++;
    double p = *pp++;
    p = p / 10.0; /* use bar to match UNESCO routines */
    /*
     * eqn 34 p.46
     */
    double c00 = 1402.388;
    double c01 =    5.03711;
    double c02 =   -5.80852e-2;
    double c03 =    3.3420e-4;
    double c04 =   -1.47800e-6;
    double c05 =    3.1464e-9;
    double c10 =  0.153563;
    double c11 =  6.8982e-4;
    double c12 = -8.1788e-6;
    double c13 =  1.3621e-7;
    double c14 = -6.1185e-10;
    double c20 =  3.1260e-5;
    double c21 = -1.7107e-6;
    double c22 =  2.5974e-8;
    double c23 = -2.5335e-10;
    double c24 =  1.0405e-12;
    double c30 = -9.7729e-9;
    double c31 =  3.8504e-10;
    double c32 = -2.3643e-12;
    double Cw = c00 
      + T * (c01 + T * (c02 + T * (c03 + T * (c04 + T * c05))))
      + p * (c10 + T * (c11 + T * (c12 + T * (c13 + T * c14)))
	     + p * (c20 + T * (c21 + T * (c22 + T * (c23 + T * c24)))
		    + p * (c30 + T * (c31 + T * c32))));
    /*
     * eqn 35. p.47
     */
    double a00 =  1.389;
    double a01 = -1.262e-2;
    double a02 =  7.164e-5;
    double a03 =  2.006e-6;
    double a04 = -3.21e-8;
    double a10 =  9.4742e-5;
    double a11 = -1.2580e-5;
    double a12 = -6.4885e-8;
    double a13 =  1.0507e-8;
    double a14 = -2.0122e-10;
    double a20 = -3.9064e-7;
    double a21 =  9.1041e-9;
    double a22 = -1.6002e-10;
    double a23 =  7.988e-12;
    double a30 =  1.100e-10;
    double a31 =  6.649e-12;
    double a32 = -3.389e-13;
    double A = a00
      + T * (a01 + T * (a02 + T * (a03 + T * a04)))
      + p * (a10 + T * (a11 + T * (a12 + T * (a13 + T * a14)))
	     + p * (a20 + T * (a21 + T * (a22 + T * a23))
		    + p * (a30 + T * (a31 + T * a32))));
    
    /*
     * eqn 36 p.47
     */
    double b00 = -1.922e-2;
    double b01 = -4.42e-5;
    double b10 =  7.3637e-5;
    double b11 =  1.7945e-7;
    double B = b00 + T * b01 + p * (b10 + T * b11);
    
    /*
     * eqn 37 p.47
     */
    double d00 =  1.727e-3;
    double d10 = -7.9836e-6;
    double D = d00 + d10 * p;
    
    /*
     * eqn 33 p.46
     */
    *value++ = Cw + S * (A + B * sqrt(S) + S * D);
  }
}

void 
theta_Bryden_1973(int *n, double *pS, double *pT, double *pp, double *value)
{
  /* Source: Bryden 1973 */
  int i;
  for (i = 0; i < *n; i++) {
    double S = *pS++;
    double T = *pT++;
    double p = *pp++;
    if (ISNA(S) || ISNA(T) || ISNA(p)) {
      *value++ = NA_REAL;
    } else {
      S -= 35.0;
      p /= 10.0; /* formula is in bars, but argument is in decibars! */
      *value++ = T
	- p * (((3.6504e-4 + T * (8.3198e-5 + T * (-5.4065e-7 + T * 4.0274e-9)))
		+ S * (1.7439e-5 - T * 2.9778e-7))
	       + p * ((8.9309e-7 + T * (-3.1628e-8 + T * 2.1987e-10) - S * 4.1057e-9)
		      + p * (-1.6056e-10 + T * 5.0484e-12)));
    }
  }
}
double
atg_UNESCO_1983(double S, double T, double p)
{
  /* Adiabatic temperature gradient, UNESCO 1983
   *
   * Usage: atg_UNESCO_1983(S, T, [P])
   *
   * Input:
   *   S = Salinity,     [PSS-78]
   *   T = Temperature,  [°C]
   *   p = Pressure,     [dbar]
   *
   * Output:
   *   Adiabatic temperature gradient,  [K/dbar]
   *
   * Check value:
   * ATG=3.255976e-4 C/dbar for S=40, T=40degC, p=10000dbar
   */
  S -= 35.0;
  return(3.5803e-5 + (8.5258e-6 + (-6.836e-8 + 6.6228e-10*T)*T)*T
	 + (1.8932e-6 - 4.2393e-8*T)*S  
	 + ((1.8741e-8 + (-6.7795e-10 + (8.733e-12 - 5.4481e-14*T)*T)*T)
	    + (-1.1351e-10 + 2.7759e-12*T)*S)*p
	 + (-4.6206e-13 + (1.8676e-14 - 2.1687e-16*T)*T)*p*p);
}

void
theta_UNESCO_1983(int *n, double *pS, double *pT, double *pp, double *ppref, double *value)
{
  /* Source: UNESCO 1983
   * check value from Fofonoff et al. (1983)
   * theta = 36.89073C at S=40, T=40, p=10000, pref=0
   */
  int i;
  for (i = 0; i < *n; i++) {
    double S = *pS++;
    double T = *pT++;
    double p = *pp++;
    double pref = *ppref++;
    if (ISNA(S) || ISNA(T) || ISNA(p) || ISNA(pref)) {
      *value++ = NA_REAL;
    } else {
      double H, XK, Q;
      H = pref - p;
      XK = H * atg_UNESCO_1983(S,T,p);
      T = T + 0.5 * XK;
      Q = XK;
      p = p + 0.5 * H;
      XK = H * atg_UNESCO_1983(S,T,p);
      T = T + 0.29289322 * (XK - Q);
      Q = 0.58578644 * XK + 0.121320344 * Q;
      XK = H * atg_UNESCO_1983(S,T,p);
      T = T + 1.707106781 * (XK - Q);
      Q = 3.414213562 * XK - 4.121320344 * Q;
      p = p + 0.5 * H;
      XK = H * atg_UNESCO_1983(S,T,p);
      *value++ = T + (XK - 2.0 * Q) / 6.0;
    }
  }
}

/*static double sig_0, p_ref, S, T;*/
void
sw_tsrho(double *pS, double *prho, double *pp, double *res)
{
  int tsrho_bisection_search (double *x, double x1, double x2, double eps, double eta);
  int bs_res;
  S = *pS;
  sig_0 = *prho;		/* target density */
  p_ref = *pp;		/* target pressure */
  *res = NA_REAL;
  if (ISNA(S) || ISNA(sig_0) || ISNA(p_ref))
    return;
  /* NOTE: do not use wide values for TLOW and THIGH, because the UNESCO
   * equation of state rho() may be odd in such limits, preventing a 
   * bisection from working.  I found this out by using a TLOW
   * value of -50.  The range below should be OK for oceanographic use.
   */
  bs_res = tsrho_bisection_search(&T, -3.0, 40.0, 0.0001, 0.0001);
  *res = T;
}

double
tsrho_f(double x)
{
  extern double p_ref, sig_0;
  void sw_rho(int *n, double *pS, double *pT, double *pp, double *res);
  double this_rho;
  int n=1;
  sw_rho(&n, &S, &x, &p_ref, &this_rho);
  /* printf(" f returning %f\n", this_rho-1000.0-sig_0); */
  return (this_rho - 1000.0 - sig_0);
}

/* bisection rootsolver
   SYNTAX
   int bis(double *x,double x1,double x2,double eps,double eta);
   DESCRIPTION: Searches for a root of f(x) over the interval [x1,x2].
   ftol = maximum allowed error in f(x)
   xresolution = maximum size of final interval bracketing  root
   RETURN VALUE
   0 if root found to within tolerance; 1 otherwise
*/
int
tsrho_bisection_search(double *x, double x1, double x2, double xresolution, double ftol)
{
  /* printf("in bisection_search(x=%f,  x1=%f,  x2=%f)\n",*x,x1,x2); */
  double tsrho_f(double x);
  double g1, g2, g;
  g1 = tsrho_f(x1);
  g2 = tsrho_f(x2);
  if (g1 * g2 > 0.0) {
    *x = NA_REAL;
    return 0;
  }
  /* printf("TOP of bs.  g1=%f   g2=%f\n",g1,g2); */
  while (fabs (g = tsrho_f (*x = (x1 + x2) / 2.0)) > ftol || fabs (x1 - x2) > xresolution) {
    /* printf("in bis loop x=%f   g=%f   g1=%f\n",*x,g,g1); */
    if (g1 * g < 0) { /* root is nearer x1 so move x2 to x */
      x2 = *x;
      g2 = g;
      /* printf("bs CASE 1.  x1=%f  x2=%f  g1=%f  g2=%f\n",x1,x2,g1,g2); */
    } else if (g2 * g < 0) { /* root is nearer x2 so move x1 to x */
      x1 = *x;
      g1 = g;
      /* printf("bs CASE 2.  x1=%f  x2=%f  g1=%f  g2=%f\n",x1,x2,g1,g2); */
    } else {	/* not bracketed BUG */
      /* printf("bs CASE 3 (not bracketed)  x1=%f  x2=%f  g1=%f  g2=%f\n",x1,x2,g1,g2); */
      *x = NA_REAL;
      return (1); /* exact solution */
    }
  }
  return (0); 		/* converged by default */
}
