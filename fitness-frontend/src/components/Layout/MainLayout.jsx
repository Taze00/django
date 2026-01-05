import BottomNav from './BottomNav';

export default function MainLayout({ children }) {
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', paddingBottom: '80px' }}>
      {children}
      <BottomNav />
    </div>
  );
}
