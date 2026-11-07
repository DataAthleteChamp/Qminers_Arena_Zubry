#include <bits/stdc++.h>
using namespace std;
struct Order {int id, qty, price; char side; bool user;};
struct Ref {char side; int price; list<Order>::iterator it;};
struct BotOrder {int id, qty, price; char side; bool accepted=false,canceling=false;};
struct Action {long long due; int id,qty,price; char side,operation;};
struct MarketBook {
 map<int,list<Order>> bids,asks;
 unordered_map<int,Ref> loc;
 long long volUser=0,nFill=0,cash=0;
 int inv=0,maxabs=0;
 double penalty=0; long long lasttime=0;
 long long submitted=0,cancels=0,failedCancel=0,rejected=0;
 map<int,list<Order>>& sideBook(char s){return s=='B'?bids:asks;}
 void remove(int id){auto it=loc.find(id);if(it==loc.end())return; auto &r=it->second;auto &m=sideBook(r.side); auto z=m.find(r.price);if(z==m.end())abort(); z->second.erase(r.it);if(z->second.empty())m.erase(z);loc.erase(it);}
 void rest(int id,char side,int qty,int price,bool user){auto &m=sideBook(side); auto &lst=m[price];lst.push_back(Order{id,qty,price,side,user});loc[id]=Ref{side,price,prev(lst.end())};}
 // return best market price and its total size; user's own orders are not counted
 pair<int,int> marketBest(char side){auto &m=sideBook(side); if(side=='B'){
   for(auto it=m.rbegin();it!=m.rend();it++){int v=0;for(auto &o:it->second)if(!o.user)v+=o.qty; if(v)return {it->first,v};}
 }else{for(auto &x:m){int v=0;for(auto &o:x.second)if(!o.user)v+=o.qty; if(v)return {x.first,v};}}
 return {0,0};}
 long long markout(){long long val=0; int remain=abs(inv);if(!remain)return 0;
   bool islong=inv>0;int fallback=0; bool any=false;
   auto &m=islong?bids:asks;
   auto consume=[&](int p,const list<Order>& ls){int sz=0;for(auto &o:ls)if(!o.user)sz+=o.qty;if(!sz)return;any=true;fallback=p;int q=min(remain,sz);val+=(long long)q*p;remain-=q;};
   if(islong){for(auto it=m.rbegin();it!=m.rend() && remain>0;it++)consume(it->first,it->second);} else {for(auto it=m.begin();it!=m.end() && remain>0;it++)consume(it->first,it->second);}
   if(!any){auto a=marketBest('A'),b=marketBest('B');fallback= a.first?a.first:(b.first?b.first:10000);}
   if(remain>0)val+=(long long)remain*fallback;
   return islong?val:-val;
 }
 void advance(long long t){if(t>lasttime && abs(inv)>100) penalty+=(t-lasttime)*.01;lasttime=t;}
};
struct Sim {
 MarketBook bk;
 unordered_map<int,BotOrder> yours;
 deque<Action> acts;
 int nextid=-1;
 int qs=2,cap=20,mode=0,refreshTicks=1,spreadBoost=0;
 double invskew=.05,imbWeight=0.;
 long long t=0,lastquote=0,totalEvent=0;
 long long prev5s=0, lastLook=0;
 double buyFlow=0,sellFlow=0;
 int lastMid=0,prevMid=0;
 unordered_map<int,int> queuedAhead;
 unordered_set<int> filledOrderIds;
 vector<int> allAhead, firstFillAhead;
 vector<long long> firstFillLagUs;
 long long statAbsinv=0,statSamples=0;
 double statScore=0;
 string file;
 long long tradeFromUs=0,tradeUntilUs=LLONG_MAX;
 void fill_user(int id,int qty,int px){auto a=yours.find(id);if(a==yours.end()) {cerr<<"FATAL unknown fill "<<id<<"\n";exit(2);} auto &u=a->second;
   if(!filledOrderIds.count(id)){
     filledOrderIds.insert(id);
     auto q=queuedAhead.find(id);if(q!=queuedAhead.end())firstFillAhead.push_back(q->second);
   }
   u.qty-=qty;
   int sign=u.side=='B'?1:-1;bk.inv+=sign*qty;bk.cash-=(long long)sign*qty*px;bk.volUser+=qty;bk.nFill++;bk.maxabs=max(bk.maxabs,abs(bk.inv));
   if(u.qty<=0)yours.erase(a);
 }
 void apply_action(Action a){
   if(a.operation=='N'){
      auto x=yours.find(a.id);if(x==yours.end())return;
      // market consumes opposite, if crossing, otherwise rest (we only quote at market touch)
      int exposure=0;for(auto &p:yours){if(p.second.side==a.side && p.second.accepted && p.second.id!=a.id)exposure+=p.second.qty;}
      int delta=a.side=='B'?1:-1;
      if(abs(bk.inv+delta*(exposure+a.qty))>1000){bk.rejected++;yours.erase(x);return;}
      x->second.accepted=true;
      int qty=a.qty;
      if(a.side=='B'){
        while(qty && !bk.asks.empty() && bk.asks.begin()->first<=a.price){int p=bk.asks.begin()->first;auto it=bk.asks.begin();bool did=false;
          for(auto o=it->second.begin();o!=it->second.end() && qty;){if(o->user){++o;continue;}int q=min(qty,o->qty);qty-=q;o->qty-=q;did=true;fill_user(a.id,q,p);if(!o->qty){bk.loc.erase(o->id);o=it->second.erase(o);}else ++o;}
          if(it->second.empty())bk.asks.erase(it); if(!did)break;
        }
      }else{
        while(qty && !bk.bids.empty() && bk.bids.rbegin()->first>=a.price){int p=bk.bids.rbegin()->first;auto it=prev(bk.bids.end());bool did=false;
          for(auto o=it->second.begin();o!=it->second.end() && qty;){if(o->user){++o;continue;}int q=min(qty,o->qty);qty-=q;o->qty-=q;did=true;fill_user(a.id,q,p);if(!o->qty){bk.loc.erase(o->id);o=it->second.erase(o);}else ++o;}
          if(it->second.empty())bk.bids.erase(it);if(!did)break;
        }
      }
      if(qty && yours.count(a.id)){
        auto &book=bk.sideBook(a.side);
        int ahead=0;auto at=book.find(a.price);if(at!=book.end())for(auto &o:at->second)ahead+=o.qty;
        queuedAhead[a.id]=ahead;allAhead.push_back(ahead);
        bk.rest(a.id,a.side,qty,a.price,true);
      }
   }else if(a.operation=='C'){
      auto x=bk.loc.find(a.id);if(x!=bk.loc.end()){bk.remove(a.id);yours.erase(a.id);bk.cancels++;}else{bk.failedCancel++;yours.erase(a.id);}
   }else if(a.operation=='M'){
       auto it=bk.loc.find(a.id);if(it!=bk.loc.end() && it->second.it->user){if(a.qty<it->second.it->qty && a.qty>=0){it->second.it->qty=a.qty;auto u=yours.find(a.id);if(u!=yours.end())u->second.qty=a.qty; if(a.qty==0){bk.remove(a.id);yours.erase(a.id);}}}
   }
 }
 void market_insert(int id,char side,int qty,int price,char tif){
   int orig=qty;
   if(side=='B'){
     while(qty && !bk.asks.empty() && bk.asks.begin()->first<=price){auto it=bk.asks.begin();int p=it->first;
       for(auto o=it->second.begin();o!=it->second.end() && qty;){int q=min(qty,o->qty);qty-=q;o->qty-=q;
         if(o->user)fill_user(o->id,q,p);
         if(!o->qty){bk.loc.erase(o->id);o=it->second.erase(o);}else ++o;
       }
       if(it->second.empty())bk.asks.erase(it);
     }
   }else{
     while(qty && !bk.bids.empty() && bk.bids.rbegin()->first>=price){auto it=prev(bk.bids.end());int p=it->first;
       for(auto o=it->second.begin();o!=it->second.end() && qty;){int q=min(qty,o->qty);qty-=q;o->qty-=q;
         if(o->user)fill_user(o->id,q,p);
         if(!o->qty){bk.loc.erase(o->id);o=it->second.erase(o);}else ++o;
       }
       if(it->second.empty())bk.bids.erase(it);
     }
   }
   if(qty && tif=='G')bk.rest(id,side,qty,price,false);
   if(tif=='F'){if(side=='B')buyFlow+=orig-qty;else sellFlow+=orig-qty;}
 }
 void submit(char s,int p,int q){if(q<=0)return; int id=nextid--;yours[id]=BotOrder{id,q,p,s,false,false};acts.push_back(Action{t+5000,id,q,p,s,'N'});bk.submitted++;}
 void cancel(BotOrder &u){if(!u.accepted || u.canceling)return;u.canceling=true;acts.push_back(Action{t+5000,u.id,0,u.price,u.side,'C'});}
 void modify(BotOrder &u,int q){if(!u.accepted || u.canceling || q>=u.qty)return;acts.push_back(Action{t+5000,u.id,q,u.price,u.side,'M'});}
 void on_book(){
   auto bid=bk.marketBest('B'),ask=bk.marketBest('A');if(!bid.first || !ask.first)return;
   double mid=(bid.first+ask.first)*.5;
   double micro=(ask.first*double(bid.second)+bid.first*double(ask.second))/(bid.second+ask.second);
   double imb=(bid.second-ask.second)/double(bid.second+ask.second);
   double center=mid+imbWeight*(micro-mid)-invskew*bk.inv;
   int targetB=max(1,min(bid.first,int(floor(center-.5))));
   int targetA=max({ask.first,int(ceil(center+.5)),targetB+1});
   int spread=ask.first-bid.first;
   if(mode==5 && spread>=3){ targetB=min(ask.first-2,targetB+1);targetA=max(targetB+1,targetA-1); }
   if(mode==6 && spread>=2){ if(imb>.15)targetB=min(ask.first-1,targetB+1);else if(imb<-.15)targetA=max(bid.first+1,targetA-1); }
   if(mode==7 && spread>=2){ if(bk.inv<0)targetB=min(ask.first-1,targetB+1);else if(bk.inv>0)targetA=max(bid.first+1,targetA-1); }
   int availableB=100-bk.inv,availableA=100+bk.inv;
   int desiredB=0,desiredA=0;
   if(mode==0 || (mode>=4 && mode<=7) || mode==9){availableB=cap-bk.inv;availableA=cap+bk.inv;desiredB=qs;desiredA=qs;}
   if(mode==1 || mode==2 || mode==3 || mode==8){
     // Adaptive: Inventory risk and directional book imbalance affect bid/ask size independently
     double scaleB=1.0,scaleA=1.0;
     // linear imbalance multiplier (negative imb means sell pressure)
     scaleB=max(.25,min(1.60,1.0+.65*imb));
     scaleA=max(.25,min(1.60,1.0-.65*imb));
     if(mode==2){ // asymmetric inventory feedback: lean hard against current position
       scaleB*=max(.12,1.0-bk.inv/110.0);
       scaleA*=max(.12,1.0+bk.inv/110.0);
     }
     if(mode==3 || mode==8){ // conservative near limit; keep 1-tick priority
       scaleB*=max(.10,1.0-bk.inv/100.0);
       scaleA*=max(.10,1.0+bk.inv/100.0);
     }
     desiredB=max(2,int(round(qs*scaleB)));
     desiredA=max(2,int(round(qs*scaleA)));
     if(spread>2){desiredB=min(qs*2, int(desiredB*1.3));desiredA=min(qs*2,int(desiredA*1.3));}
   }
   int liveB=0,liveA=0;
   for(auto &kv:yours){auto &o=kv.second;if(o.side=='B')liveB+=o.qty;else liveA+=o.qty;}
   // cancel hysteresis: replace old quote only when target price materially changes; this saves priority
   for(auto &kv:yours){auto &u=kv.second;
     int desired=u.side=='B'?targetB:targetA;
     int d=u.side=='B'?desiredB:desiredA;
     if(u.accepted&&!u.canceling){
       // for all modes price hysteresis (mode0 exactly original)
       if(mode==4){
         bool adverse = u.side=='B' ? u.price>desired : u.price<desired;
         bool far = abs(desired-u.price)>=2;
         // Only keep favorable older quotes if they are close to touch; old queue priority is valuable.
         if(adverse || far)cancel(u);
       }else if(abs(desired-u.price)>=(mode==0?1:refreshTicks))cancel(u);
       else if(mode>=2 && u.qty>d*2 && d>1) modify(u,d);
     }
   }
   bool hasB=false,hasA=false;
   for(auto &kv:yours){auto &u=kv.second;if(u.side=='B')hasB=true;else hasA=true;}
   if(mode==9){
     for(char side:{'B','A'}){
       int price=side=='B'?targetB:targetA;
       int existing=side=='B'?liveB:liveA;
       int desired=side=='B'?desiredB:desiredA;
       int headroom=side=='B'?availableB:availableA;
       bool incompatible=false;
       for(auto &kv:yours){auto &u=kv.second; if(u.side==side && (u.price!=price || u.canceling))incompatible=true;}
       if(incompatible)continue;
       int q=min(desired-existing,headroom-existing);
       if(q>0)submit(side,price,q);
     }
   }else{
     if(!hasB){int q=min(desiredB,availableB-liveB);if(q>0)submit('B',targetB,q);}
     if(!hasA){int q=min(desiredA,availableA-liveA);if(q>0)submit('A',targetA,q);}
   }
 }
 static long long parse_time_us(const string &s){auto p=s.find('.');if(p==string::npos)return stoll(s)*1000000LL; long long whole=stoll(s.substr(0,p));string fr=s.substr(p+1);fr.resize(6,'0');return whole*1000000LL+stoll(fr);}
 void run(string path){ifstream f(path);if(!f){cerr<<"cannot open "<<path<<"\n";exit(1);} string line;getline(f,line);long long t0=-1,prev=-1;
  while(getline(f,line)){
    string_view ln(line); int cuts[7],ncut=0;for(int i=0;i<(int)ln.size();i++)if(ln[i]==',')cuts[ncut++]=i;
    if(ncut<6)continue;
    string s(ln.substr(0,cuts[0])); t=parse_time_us(s);
    if(t0<0)t0=t;
    if(t>tradeUntilUs)break;
    if(prev>=0)bk.advance(t);else bk.lasttime=t;prev=t;
    while(!acts.empty()&&acts.front().due<=t){auto a=acts.front();acts.pop_front();apply_action(a);}
    auto get=[&](int i)->string_view{int a=i==0?0:cuts[i-1]+1;int e=i<ncut?cuts[i]:(int)ln.size();return ln.substr(a,e-a);};
    string_view op=get(1);int id=atoi(string(get(2)).c_str());
    if(op=="Insert"){
      char side=get(3)[0];int qty=atoi(string(get(4)).c_str());int px=atoi(string(get(5)).c_str());char tif=get(6).empty()?'G':get(6)[0];market_insert(id,side,qty,px,tif);
    }else if(op=="Cancel")bk.remove(id);
    if(t>=tradeFromUs)on_book();
    totalEvent++;
    if(totalEvent%20000==0){statAbsinv+=abs(bk.inv);statSamples++;}
  }
  int mb=bk.marketBest('B').first,ma=bk.marketBest('A').first;
  double pnl=bk.cash + bk.markout() - bk.penalty;
  auto percentile=[](vector<int> v,double p){if(v.empty())return -1;size_t at=min(v.size()-1,(size_t)(p*(v.size()-1)));nth_element(v.begin(),v.begin()+at,v.end());return v[at];};
  cout<<fixed<<setprecision(2)<<"{\"mode\":"<<mode<<",\"size\":"<<qs<<",\"cap\":"<<cap<<",\"hysteresis\":"<<refreshTicks<<",\"pnl\":"<<pnl<<",\"cash\":"<<bk.cash<<",\"inv\":"<<bk.inv<<",\"markout\":"<<bk.markout()<<",\"penalty\":"<<bk.penalty<<",\"fills\":"<<bk.nFill<<",\"volume\":"<<bk.volUser<<",\"max_abs_inventory\":"<<bk.maxabs<<",\"submissions\":"<<bk.submitted<<",\"cancels\":"<<bk.cancels<<",\"failed_cancels\":"<<bk.failedCancel<<",\"rejections\":"<<bk.rejected<<",\"accepted_queue_ahead_p50\":"<<percentile(allAhead,.5)<<",\"accepted_queue_ahead_p90\":"<<percentile(allAhead,.9)<<",\"firstfilled_queue_ahead_p50\":"<<percentile(firstFillAhead,.5)<<",\"firstfilled_queue_ahead_p90\":"<<percentile(firstFillAhead,.9)<<",\"orders_resting_count\":"<<allAhead.size()<<",\"orders_ever_filled\":"<<firstFillAhead.size()<<",\"events\":"<<totalEvent<<",\"duration_seconds\":"<<(t-t0)*1e-6<<",\"bid\":"<<mb<<",\"ask\":"<<ma<<"}"<<endl;
 }
};
int main(int argc,char **argv){if(argc<5){cerr<<"usage: replay FILE MODE QUOTE_SIZE CAP [HYSTERESIS]\n";return 1;}Sim s;s.qs=atoi(argv[3]);s.cap=atoi(argv[4]);s.mode=atoi(argv[2]); if(argc>5)s.refreshTicks=atoi(argv[5]);if(argc>6)s.tradeFromUs=(long long)(atof(argv[6])*1e6);if(argc>7)s.tradeUntilUs=(long long)(atof(argv[7])*1e6);s.run(argv[1]);}
