// Independent implementation of supplement S2--S5 and an explicit least-squares convention.
// Reads only our analytic-test configuration. Never opens the authors' PDFs or ZIPs.
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>
using Vec=std::vector<double>;
using Mat=std::vector<Vec>;
const double pi=std::acos(-1.);
double log_ratio(double a,double b) {
    if(!std::isfinite(a)||!std::isfinite(b)||a<=0||b<=0) throw std::domain_error("positive finite inputs required");
    return std::log10(a)-std::log10(b);
}
double mean_power(const Vec& x) {
    if(x.empty()) throw std::domain_error("empty window");
    double q=0; for(double v:x) q+=v*v; return q/x.size();
}
Vec spectrum(const Vec& x) {
    // One-sided rectangular-window periodogram, mean removed, normalized for Parseval.
    size_t n=x.size(); if(n<2) throw std::domain_error("short window");
    double mu=std::accumulate(x.begin(),x.end(),0.)/n;
    Vec p(n/2+1);
    for(size_t k=0;k<p.size();k++) {
        double re=0,im=0;
        for(size_t j=0;j<n;j++) {double a=2*pi*k*j/n; re+=(x[j]-mu)*std::cos(a); im-=(x[j]-mu)*std::sin(a);}
        double factor=(k==0 || (n%2==0 && k==n/2))?1.:2.;
        p[k]=factor*(re*re+im*im)/(double(n)*n);
    }
    return p;
}
double band(const Vec& p,double fs,size_t n,double lo,double hi) {
    double q=0; for(size_t k=0;k<p.size();k++) {double f=k*fs/n; if(f>=lo&&f<=hi) q+=p[k];} return q;
}
double fi(const Vec& x,const std::map<std::string,double>& c) {
    Vec p=spectrum(x);
    return log_ratio(band(p,c.at("fs"),x.size(),c.at("high_min"),c.at("high_max")),
                     band(p,c.at("fs"),x.size(),c.at("low_min"),c.at("low_max")));
}
Vec solve(Mat a,Vec b) {
    size_t n=b.size();
    for(size_t k=0;k<n;k++) {
        size_t pivot=k; for(size_t i=k+1;i<n;i++) if(std::abs(a[i][k])>std::abs(a[pivot][k])) pivot=i;
        if(std::abs(a[pivot][k])<1e-12) throw std::domain_error("unanchored/singular magnitude problem");
        std::swap(a[k],a[pivot]); std::swap(b[k],b[pivot]);
        for(size_t i=k+1;i<n;i++) {double f=a[i][k]/a[k][k]; for(size_t j=k;j<n;j++) a[i][j]-=f*a[k][j]; b[i]-=f*b[k];}
    }
    Vec x(n); for(int i=int(n)-1;i>=0;i--) {double s=b[i]; for(size_t j=i+1;j<n;j++) s-=a[i][j]*x[j]; x[i]=s/a[i][i];} return x;
}
Vec magnitude_fit(const Vec& amplitude,const Vec& prior,double lambda,bool reverse=false) {
    size_t n=amplitude.size(); Mat a(n,Vec(n)); Vec b(n);
    for(size_t i=0;i<n;i++) for(size_t j=i+1;j<n;j++) {
        size_t u=reverse?j:i,v=reverse?i:j;
        double w=1./(j-i),d=log_ratio(amplitude[u],amplitude[v]);
        a[u][u]+=w; a[v][v]+=w; a[u][v]-=w; a[v][u]-=w; b[u]+=w*d; b[v]-=w*d;
    }
    for(size_t i=0;i<n;i++) {a[i][i]+=lambda; b[i]+=lambda*prior[i];}
    return solve(a,b);
}
double max_error(const Vec& x,const Vec& y) {double e=0; for(size_t i=0;i<x.size();i++) e=std::max(e,std::abs(x[i]-y[i])); return e;}
int main(int argc,char** argv) {
 try {
    if(argc!=3) throw std::runtime_error("usage: method_checks config/method_checks.cfg data");
    std::ifstream f(argv[1]); if(!f) throw std::runtime_error("missing configuration");
    std::map<std::string,double> c; std::string line;
    while(std::getline(f,line)) {if(line.empty()||line[0]=='#') continue; auto k=line.find(' '); c[line.substr(0,k)]=std::stod(line.substr(k+1));}
    int n=int(c.at("fs")*c.at("duration"));
    if(n<2||c.at("high_max")>=c.at("fs")/2) throw std::runtime_error("invalid spectral configuration");
    auto output=[&](std::string name) {std::ofstream o(std::string(argv[2])+"/"+name); if(!o) throw std::runtime_error("output failure"); o<<std::setprecision(16); return o;};
    auto checks=output("checks.csv"); checks<<"name,error,tolerance,pass\n"; int failures=0;
    auto check=[&](std::string name,double error,double tol) {bool ok=std::isfinite(error)&&error<=tol; checks<<name<<","<<error<<","<<tol<<","<<ok<<"\n"; if(!ok) failures++;};
    auto rejects=[&](std::string name,double a,double b) {bool yes=false; try {log_ratio(a,b);} catch(const std::domain_error&) {yes=true;} check(name,yes?0:1,0);};
    check("equal_amplitudes",std::abs(log_ratio(7,7)),1e-14);
    check("decade_amplitude",std::abs(log_ratio(100,10)-1),1e-14);
    check("ratio_reversal",std::abs(log_ratio(3,7)+log_ratio(7,3)),1e-14);
    check("common_station_gain",std::abs(log_ratio(3,7)-log_ratio(300,700)),1e-14);
    rejects("zero_amplitude_rejected",0,1); rejects("negative_power_rejected",1,-1);
    auto scale=output("scaling.csv"); scale<<"amplitude_ratio,delta_m,snr_db,expected_delta_m,expected_snr_db\n";
    for(int i=-8;i<=8;i++) {double e=i*.25,r=std::pow(10.,e); scale<<r<<","<<log_ratio(r,1)<<","<<10*log_ratio(r*r,1)<<","<<e<<","<<20*e<<"\n";}
    auto spec=output("frequency_index.csv"); spec<<"amplitude_ratio,fi,expected_fi,error\n";
    auto waveform=output("waveform.csv"); waveform<<"time_s,signal\n";
    Vec base;
    for(int q=-6;q<=6;q++) {
        double e=q*.25,r=std::pow(10.,e); Vec x(n);
        for(int j=0;j<n;j++) {double t=j/c.at("fs"); x[j]=std::sin(2*pi*c.at("low_tone")*t)+r*std::sin(2*pi*c.at("high_tone")*t);}
        double v=fi(x,c),err=std::abs(v-2*e); check("fi_mixture_"+std::to_string(q+6),err,1e-10);
        spec<<r<<","<<v<<","<<2*e<<","<<err<<"\n";
        if(q==0) {base=x; for(int j=0;j<n;j++) waveform<<j/c.at("fs")<<","<<x[j]<<"\n";}
    }
    Vec p=spectrum(base); check("parseval",std::abs(std::accumulate(p.begin(),p.end(),0.)-mean_power(base)),1e-10);
    Vec shifted=base; std::rotate(shifted.begin(),shifted.begin()+17,shifted.end()); check("fi_circular_shift",std::abs(fi(base,c)-fi(shifted,c)),1e-10);
    Vec scaled=base; for(double& v:scaled) v*=7; check("fi_gain",std::abs(fi(base,c)-fi(scaled,c)),1e-10);
    Vec noise200(200),signal500(500); for(size_t j=0;j<noise200.size();j++) noise200[j]=std::sin(2*pi*3*j/c.at("fs"));
    for(size_t j=0;j<signal500.size();j++) signal500[j]=2*std::sin(2*pi*3*j/c.at("fs"));
    check("snr_5s_2s_windows",std::abs(10*log_ratio(mean_power(signal500),mean_power(noise200))-10*std::log10(4)),1e-10);
    Vec truth{0.,.3,-.2,.8},amps; for(double v:truth) amps.push_back(std::pow(10.,v));
    Vec exact=magnitude_fit(amps,truth,1);
    check("magnitude_exact_recovery",max_error(exact,truth),1e-12);
    check("magnitude_pair_order",max_error(exact,magnitude_fit(amps,truth,1,true)),1e-12);
    Vec prior=truth; for(double& v:prior) v+=.7;
    Vec ref=truth; for(double& v:ref) v+=.7;
    check("magnitude_gauge_shift",max_error(magnitude_fit(amps,prior,1),ref),1e-12);
    bool singular=false; try{magnitude_fit(amps,truth,0);}catch(const std::domain_error&){singular=true;}
    check("unanchored_problem_rejected",singular?0:1,0);
    auto inv=output("regularization.csv"); inv<<"lambda,rmse_magnitude\n";
    prior=truth; prior[0]+=.2; prior[1]-=.1; prior[2]+=.1; prior[3]-=.2;
    for(double lambda:{.001,.01,.1,1.,10.,100.}) {Vec sol=magnitude_fit(amps,prior,lambda);double ss=0;for(size_t j=0;j<sol.size();j++)ss+=(sol[j]-truth[j])*(sol[j]-truth[j]);inv<<lambda<<","<<std::sqrt(ss/sol.size())<<"\n";}
    auto gate=output("thresholds.csv");gate<<"ncc_sum,methods_S7_keep,caption_S9_keep\n";
    for(int sum:{99,100,101}) gate<<sum<<","<<(sum>=100)<<","<<(sum>100)<<"\n";
    std::cout<<"Documented-equation checks: "<<(failures?"FAIL":"PASS")<<"; failed checks="<<failures<<"\n";
    return failures?1:0;
 } catch(const std::exception& e) {std::cerr<<e.what()<<"\n";return 2;}
}
